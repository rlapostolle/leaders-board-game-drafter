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

unit_defs = data["characters"]

for unit in unit_defs:
    unit.setdefault("do_counter", [])
    for other in unit_defs:
        for other_counter in other["counters"]:
            if other_counter["name"] == unit["name"]:
                unit["do_counter"].append(other)

for unit in unit_defs:
    cols = st.columns([0.2, 0.8])
    unit_id = unit["name"]
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
for unit in unit_defs:
    score = unit["rating"]
    # check if the unit is in own_units or oppo_units
    for oppo_avail_unit_id in st.session_state.oppo_units + st.session_state.available_units:
        counters = unit["counters"] if unit["counters"] else []
        found = next(filter(lambda x : x["name"] == oppo_avail_unit_id, counters), None)
        if found != None:
            score -= found["rating"]
    for oppo_unit_id in st.session_state.oppo_units:
        do_counter = unit["do_counter"] if unit["do_counter"] else []
        found = next(filter(lambda x : x["name"] == oppo_unit_id, do_counter), None)
        if found != None:
            score += found["rating"]
    if score < min(20, unit["rating"]):
        score = min(20, unit["rating"])
    ordered_units.append((unit, score))


ordered_units.sort(key=lambda x: x[1], reverse=True)

with st.sidebar:
    for (unit, score) in ordered_units:
        unit_id = unit["name"]
        img_path = os.path.join(image_folder, unit["img"])
        
        containers = st.columns([0.3, 0.4, 0.3])
        containers[0].image(img_path, width=50)
        if unit_id in st.session_state.own_units:
            color = "green"
        if unit_id in st.session_state.ban_units:
            color = "red"
        if unit_id in st.session_state.oppo_units:
            color = "violet"
        if unit_id in st.session_state.available_units:
            color = None
        containers[1].markdown(':' + color + '[' + unit["name"] + ']' if color else unit["name"])
        containers[2].text(f"Score: {score:.02f}")