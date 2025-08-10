
import os, io, math, random
import pandas as pd
import numpy as np
import streamlit as st
from PIL import Image, ImageDraw

st.set_page_config(page_title="Glaze Predictor (with Images + Links)", layout="wide")

INV_PATH = "glaze_inventory.csv"
RULES_PATH = "glaze_rules.csv"
EXP_PATH = "glaze_experiments.csv"
IMG_DIR = "images"

st.title("Glaze Combination Predictor — Visual Rules")
st.caption("Defaults: Cone **6 (medium speed)** • Clay: **B-Mix** • Bisque: **Cone 04**")

@st.cache_data
def load_data():
    inv = pd.read_csv(INV_PATH)
    try:
        rules = pd.read_csv(RULES_PATH)
    except Exception:
        rules = pd.DataFrame(columns=[
            "base_glaze_id","over_glaze_id","clear_coat",
            "run_risk_delta","lighten_factor","cover_factor","variegation_boost",
            "image_url","local_image","preview_base_hex","preview_overlay_hex",
            "reference_url","notes"
        ])
    for col in ["image_url","local_image","preview_base_hex","preview_overlay_hex","reference_url","notes"]:
        if col not in rules.columns:
            rules[col] = ""
    try:
        exp = pd.read_csv(EXP_PATH)
    except Exception:
        exp = pd.DataFrame(columns=[
            "base_glaze_id","overlay_glaze_id","clear_coat",
            "base_coats","overlay_coats","application","placement","texture_level",
            "observed_run_label","observed_overlay_coverage_pct","observed_variegation_pct",
            "firing_cone","kiln_notes","notes"
        ])
    return inv, rules, exp

def hex_to_rgb(h, default=(200,200,200)):
    try:
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return default

def generate_preview(base_hex, overlay_hex, cover, run_score, variegation, size=220):
    from PIL import Image, ImageDraw
    base_rgb = hex_to_rgb(base_hex, (210,210,210))
    over_rgb = hex_to_rgb(overlay_hex, (140,170,160))
    img = Image.new("RGB", (size, size), base_rgb)
    draw = ImageDraw.Draw(img)
    alpha = int(180 * cover)
    overlay_layer = Image.new("RGBA", (size, size), over_rgb + (alpha,))
    img = Image.alpha_composite(img.convert("RGBA"), overlay_layer).convert("RGB")
    n_drips = int(6 + 18 * min(1.0, run_score/1.2))
    max_len = int(size * min(0.9, run_score/1.6))
    for i in range(n_drips):
        x = random.randint(0, size-1)
        length = random.randint(int(max_len*0.3), max_len)
        width = random.randint(2, 5)
        drip = Image.new("RGBA", (width, length), over_rgb + (min(200, 120+alpha)))
        img.paste(drip, (x, random.randint(0, int(size*0.2))), drip)
    speckles = int(400 * variegation)
    for _ in range(speckles):
        x = random.randint(0, size-1); y = random.randint(0, size-1)
        img.putpixel((x,y), tuple(min(255, c+random.randint(-15,15)) for c in img.getpixel((x,y))))
    b = Image.new("RGB", (size+8, size+8), (240,240,240))
    b.paste(img, (4,4))
    return b

inv, rules, exp = load_data()

use_rules = st.toggle("Use saved rules in predictions", value=False)

c1, c2 = st.columns([1,1])
with c1:
    st.subheader("Choose a combo")
    base = st.selectbox("Base glaze", inv["glaze_id"], format_func=lambda gid: inv.loc[inv.glaze_id==gid, "name"].values[0])
    overlay = st.selectbox("Overlay glaze (or 'None')", ["(none)"] + inv["glaze_id"].tolist(),
                           format_func=lambda gid: "None" if gid=="(none)" else inv.loc[inv.glaze_id==gid, "name"].values[0] if gid in list(inv.glaze_id) else "None")
    clear_coat = st.selectbox("Clear coat", ["none","gloss","satin_matte"])
    base_coats = st.slider("Base thickness (coats)", 1, 5, 2)
    overlay_coats = st.slider("Overlay thickness (coats)", 0, 4, 1)
    application = st.selectbox("Application", ["brushed","dipped","poured"])
    placement = st.selectbox("Placement", ["flat","vertical_wall","rim","inside_bowl","over_texture"])
    texture_level = st.slider("Texture level", 0, 10, 4)

def get_row(gid):
    r = inv[inv.glaze_id == gid]
    return r.iloc[0] if len(r) else None
def safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default

base_row = get_row(base)
over_row = get_row(overlay) if overlay != "(none)" else None
base_flow = safe_float(base_row.flow_0to1)
over_flow = safe_float(over_row.flow_0to1) if over_row is not None else 0.0
over_opacity = safe_float(over_row.opacity_0to1) if over_row is not None else 0.0

run_delta = lighten_factor = cover_factor = variegation_boost = 0.0
rule_note = ""
rule_img_url = ""
rule_local_img = ""
ref_url = ""
prev_base_hex = ""
prev_overlay_hex = ""
if use_rules and overlay != "(none)":
    r = rules[(rules.base_glaze_id==base) & (rules.over_glaze_id==overlay) & (rules.clear_coat==clear_coat)]
    if len(r):
        r0 = r.iloc[0]
        run_delta = safe_float(r0.get("run_risk_delta", 0.0))
        lighten_factor = safe_float(r0.get("lighten_factor", 0.0))
        cover_factor = safe_float(r0.get("cover_factor", 0.0))
        variegation_boost = safe_float(r0.get("variegation_boost", 0.0))
        rule_note = str(r0.get("notes", ""))
        rule_img_url = str(r0.get("image_url", ""))
        rule_local_img = str(r0.get("local_image", ""))
        prev_base_hex = str(r0.get("preview_base_hex", "")) or "#cfcfcf"
        prev_overlay_hex = str(r0.get("preview_overlay_hex", "")) or "#7aa69a"
        ref_url = str(r0.get("reference_url", ""))

coats_weight = base_coats*0.1 + overlay_coats*0.2
placement_risk = {"flat":0.0,"vertical_wall":0.3,"rim":0.4,"inside_bowl":0.35,"over_texture":0.25}[placement]
app_risk = {"brushed":0.05,"dipped":0.1,"poured":0.2}[application]
run_risk = np.clip(0.4*base_flow + 0.7*over_flow + coats_weight + placement_risk + app_risk + (texture_level*0.02) + run_delta, 0.0, 1.8)
run_label = "Low" if run_risk < 0.5 else ("Medium" if run_risk < 1.0 else "High")
overlay_cover = np.clip((over_opacity*0.6 + cover_factor) * (overlay_coats/3.0), 0.0, 1.0)
variegation = np.clip((texture_level/10.0)*0.4 + variegation_boost + (0.2 if placement=="over_texture" else 0.0), 0.0, 1.0)

# Finish (simple)
if clear_coat == "satin_matte":
    finish = "satin/matte"
elif clear_coat == "gloss":
    finish = "gloss"
else:
    finish = base_row.finish if overlay == "(none)" else (over_row.finish if over_row is not None else base_row.finish)

def display_rule_visual():
    if use_rules and overlay != "(none)":
        r = rules[(rules.base_glaze_id==base) & (rules.over_glaze_id==overlay) & (rules.clear_coat==clear_coat)]
        if len(r):
            r0 = r.iloc[0]
            url = r0.get("image_url","")
            local = r0.get("local_image","")
            if url:
                st.image(url, caption="Official image", use_column_width=True)
            elif local and os.path.exists(os.path.join(IMG_DIR, local)):
                st.image(os.path.join(IMG_DIR, local), caption="Your reference", use_column_width=True)
            else:
                img = generate_preview(prev_base_hex, prev_overlay_hex, float(overlay_cover), float(run_risk), float(variegation))
                st.image(img, caption="Generated preview", use_column_width=False)
            ref = r0.get("reference_url","")
            if ref:
                st.markdown(f"[View official chart/reference]({ref})")

with c2:
    st.subheader("Prediction")
    st.markdown(f"**Base:** {base_row['brand']} {base_row['name']}")
    st.markdown(f"**Overlay:** {'None' if over_row is None else (over_row['brand'] + ' ' + over_row['name'])}")
    st.metric("Run risk", run_label)
    st.metric("Overlay coverage", f"{int(overlay_cover*100)}%")
    st.metric("Variegation", f"{int(variegation*100)}%")
    st.markdown(f"**Finish:** {finish}")
    if rule_note and use_rules:
        st.info(f"Rule note: {rule_note}")
    display_rule_visual()

st.divider()
st.header("Rule Builder (with images + link)")
rb1, rb2 = st.columns([1,1])
with rb1:
    rb_base = st.selectbox("Base glaze (for rule)", inv["glaze_id"], key="rb_base")
    rb_overlay = st.selectbox("Overlay glaze (for rule)", inv["glaze_id"], key="rb_overlay")
    rb_clear = st.selectbox("Clear coat (for rule)", ["none","gloss","satin_matte"], key="rb_clear")

    # Numeric fields
    run_delta = st.number_input("Run risk delta (−1.0..+1.0)", -1.0, 1.0, 0.0, 0.05)
    lighten_factor = st.number_input("Lightening factor (0..1)", 0.0, 1.0, 0.0, 0.05)
    cover_factor = st.number_input("Extra cover factor (0..1)", 0.0, 1.0, 0.2, 0.05)
    variegation_boost = st.number_input("Variegation boost (0..1)", 0.0, 1.0, 0.1, 0.05)

    # Visual fields
    image_url = st.text_input("Official image URL (if available)")
    local_image = st.text_input("Local image filename in 'images/'")
    colA, colB = st.columns(2)
    with colA:
        preview_base_hex = st.color_picker("Preview base color", value="#cfcfcf")
    with colB:
        preview_overlay_hex = st.color_picker("Preview overlay color", value="#7aa69a")
    reference_url = st.text_input("Reference page/ PDF URL")
    rule_notes = st.text_input("Notes (what you saw)")

    if st.button("Save rule"):
        # Read, replace or append, then save
        rules_df = pd.read_csv(RULES_PATH) if os.path.exists(RULES_PATH) else pd.DataFrame()
        mask = (len(rules_df) and
                (rules_df["base_glaze_id"]==rb_base) &
                (rules_df["over_glaze_id"]==rb_overlay) &
                (rules_df["clear_coat"]==rb_clear))
        if isinstance(mask, pd.Series) and mask.any():
            idx = rules_df.index[mask][0]
            rules_df.loc[idx, ["run_risk_delta","lighten_factor","cover_factor","variegation_boost",
                               "image_url","local_image","preview_base_hex","preview_overlay_hex","reference_url","notes"]] = [
                run_delta, lighten_factor, cover_factor, variegation_boost,
                image_url, local_image, preview_base_hex, preview_overlay_hex, reference_url, rule_notes
            ]
        else:
            new_row = pd.DataFrame([{
                "base_glaze_id": rb_base, "over_glaze_id": rb_overlay, "clear_coat": rb_clear,
                "run_risk_delta": run_delta, "lighten_factor": lighten_factor, "cover_factor": cover_factor,
                "variegation_boost": variegation_boost, "image_url": image_url, "local_image": local_image,
                "preview_base_hex": preview_base_hex, "preview_overlay_hex": preview_overlay_hex,
                "reference_url": reference_url, "notes": rule_notes
            }])
            rules_df = pd.concat([rules_df, new_row], ignore_index=True)
        rules_df.to_csv(RULES_PATH, index=False)
        st.success("Rule saved/updated.")

with rb2:
    st.subheader("Upload a local reference image")
    upl = st.file_uploader("Choose an image", type=["jpg","jpeg","png","webp"])
    lf = st.text_input("Save as filename (e.g., pc59_over_pc32.jpg)")
    if upl and st.button("Save image"):
        os.makedirs(IMG_DIR, exist_ok=True)
        if lf:
            with open(os.path.join(IMG_DIR, lf), "wb") as f:
                f.write(upl.read())
            st.success(f"Saved to {IMG_DIR}/{lf}")
        else:
            st.warning("Enter a filename before saving.")
    st.subheader("Existing rules")
    try:
        rules_now = pd.read_csv(RULES_PATH)
        st.dataframe(rules_now, use_container_width=True, height=320)
    except Exception:
        st.info("No rules yet.")
