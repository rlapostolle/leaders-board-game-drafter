import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import os, base64, json

def get_image_as_base64(img_path):
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

with open(os.path.join(os.getcwd(), "config.json"), "r", encoding="utf8") as f:
    data = json.load(f)
image_folder = os.path.join(os.getcwd(), "images")

if 'own_units' not in st.session_state:
    st.session_state.own_units = []
if 'oppo_units' not in st.session_state:
    st.session_state.oppo_units = []
if 'ban_units' not in st.session_state:
    st.session_state.ban_units = []
if 'available_units' not in st.session_state:
    st.session_state.available_units = []

unit_defs = dict([(u["name"], u) for u in data["characters"] ])

for unit_id, unit in unit_defs.items():
    unit.setdefault("do_counter", [])
    for other_id, other in unit_defs.items():
        for other_counter in other["counters"]:
            if other_counter["name"] == unit_id:
                print (f"Adding {unit_id} to {other_id}'s do_counter")
                unit["do_counter"].append({"name": other["name"], "rating": other_counter["rating"]})

for unit_id, unit in unit_defs.items():
    cols = st.columns([0.2, 0.8])
    img_path = os.path.join(image_folder, unit["img"])

    cols[0].image(img_path, width=100)
    container = cols[1].container()
    rating = unit["rating"]
    container.text(unit["name"])
    container.text(f"Rating: {rating:.0f}")
    selection = container.segmented_control("State", ["Avail", "Pick", "Ban", "Oppo"], selection_mode="single", default="Avail", key=f"segmented:{unit_id}", label_visibility="collapsed")
    if selection == "Oppo":
        if unit_id not in st.session_state.oppo_units:
            st.session_state.oppo_units.append(unit_id)
        if unit_id in st.session_state.own_units:
            st.session_state.own_units.remove(unit_id)
        if unit_id in st.session_state.ban_units:
            st.session_state.ban_units.remove(unit_id)
        if unit_id in st.session_state.available_units:
            st.session_state.available_units.remove(unit_id)
    elif selection == "Avail":
        if unit_id in st.session_state.own_units:
            st.session_state.own_units.remove(unit_id)
        if unit_id in st.session_state.oppo_units:
            st.session_state.oppo_units.remove(unit_id)
        if unit_id in st.session_state.ban_units:
            st.session_state.ban_units.remove(unit_id)
        if unit_id not in st.session_state.available_units:
            st.session_state.available_units.append(unit_id)
    elif selection == "Ban":
        if unit_id not in st.session_state.ban_units:
            st.session_state.ban_units.append(unit_id)
        if unit_id in st.session_state.own_units:
            st.session_state.own_units.remove(unit_id)
        if unit_id in st.session_state.oppo_units:
            st.session_state.oppo_units.remove(unit_id)
        if unit_id in st.session_state.available_units:
            st.session_state.available_units.remove(unit_id)
    elif selection == "Pick":
        if unit_id not in st.session_state.own_units:
            st.session_state.own_units.append(unit_id)
        if unit_id in st.session_state.oppo_units:
            st.session_state.oppo_units.remove(unit_id)
        if unit_id in st.session_state.ban_units:
            st.session_state.ban_units.remove(unit_id)
        if unit_id in st.session_state.available_units:
            st.session_state.available_units.remove(unit_id)

ordered_units = []
unit_scores = {}
for unit_id, unit in unit_defs.items():
    score = unit["rating"]
    # check if the unit is in own_units or oppo_units
    countered_by = unit["counters"] if unit["counters"] else []
    if unit_id in st.session_state.available_units:
        for oppo_avail_unit_id in st.session_state.oppo_units + (st.session_state.available_units if len(st.session_state.oppo_units) < 4 else []):
            found = next(filter(lambda x : x["name"] == oppo_avail_unit_id, countered_by), None)
            if found != None:
                score -= found["rating"]
    if unit_id in st.session_state.own_units:
        for oppo_unit_id in st.session_state.oppo_units:
            # only remove the score if if got countered by the opponent's unit
            #found = next(filter(lambda x : x["name"] == oppo_unit_id, do_counter), None)
            #if found != None:
            #    score += found["rating"]
            found = next(filter(lambda x : x["name"] == oppo_unit_id, countered_by), None)
            if found != None:
                score -= found["rating"]
    if unit_id in st.session_state.oppo_units:
        for own_unit_id in st.session_state.own_units:
            # only remove the score if it got countered by our unit
            #found = next(filter(lambda x : x["name"] == own_unit_id, do_counter), None)
            #if found != None:
            #    score += found["rating"]
            found = next(filter(lambda x : x["name"] == own_unit_id, countered_by), None)
            if found != None:
                score -= found["rating"]

    if score < min(20, unit["rating"]):
        score = min(20, unit["rating"])
    ordered_units.append((unit, score))
    unit_scores[unit_id] = score

for unit_id, unit in unit_defs.items():
    if unit_id in st.session_state.available_units:
        do_counter = unit["do_counter"] if unit["do_counter"] else []
        for oppo_avail_unit_id in st.session_state.oppo_units:
            found = next(filter(lambda x : x["name"] == oppo_avail_unit_id, do_counter), None)
            if found != None:
                found_score = unit_scores[found["name"]]
                diff = found_score - max(20, found_score - found["rating"])
                unit_scores[unit_id] += min(found["rating"], diff)
                ordered_units = list(filter(lambda x: x[0]["name"] != unit_id, ordered_units))
                ordered_units.append((unit, unit_scores[unit_id]))

ordered_units.sort(key=lambda x: x[1], reverse=True)

with st.sidebar:

    st.markdown("### Own Team Score")
    own_score = sum(unit_scores[unit] for unit in st.session_state.own_units)
    st.text(f"{own_score:.0f}")
    st.markdown("### Opponent Team Score")
    oppo_score = sum(unit_scores[unit] for unit in st.session_state.oppo_units)
    st.text(f"{oppo_score:.0f}")

    st.markdown("### Units Overall Score")
    for (unit, score) in ordered_units:
        unit_id = unit["name"]
        if unit_id in st.session_state.ban_units:
            continue
        img_path = os.path.join(image_folder, unit["img"])
        
        containers = st.columns([0.3, 0.4, 0.3])
        containers[0].image(img_path, width=50)
        if unit_id in st.session_state.own_units:
            containers[1].markdown(':green[' + unit["name"] + ']')
        if unit_id in st.session_state.oppo_units:
            containers[1].markdown(':red[' + unit["name"] + ']')
        if unit_id in st.session_state.available_units:
            containers[1].markdown(unit["name"])
        containers[2].text(f"Score: {score:.02f}")

    st.markdown("### Banned Units")
    for (unit, score) in ordered_units:
        unit_id = unit["name"]
        if unit_id not in st.session_state.ban_units:
            continue
        containers = st.columns([0.3, 0.4, 0.3])
        img_path = os.path.join(image_folder, unit["img"])
        containers[0].image(img_path, width=50)
        containers[1].markdown('~~' + unit["name"] + '~~')