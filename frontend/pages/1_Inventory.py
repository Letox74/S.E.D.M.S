from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from frontend.utils import check_for_password_verification, api_client
from internal.schemas.device_models import DeviceTypes, DeviceStatus, DeviceUpdate, DeviceCreate

st.set_page_config(layout="wide")

TTL_CACHE_TIME = 60 * 30  # 30 minutes


# api call functions
@st.cache_data(ttl=TTL_CACHE_TIME)
def fetch_device_fleet() -> Any:
    return api_client.request("GET", "/devices/").data


def update_device(data: DeviceUpdate, device_id: str) -> None | str:
    result = api_client.request("PATCH", f"/devices/{device_id}", json={"data": data.model_dump()})
    return result.data["detail"] if not result.is_success else None

def delete_device(device_id: str) -> None:
    api_client.request("DELETE", f"/devices/{device_id}")


def register_new_device(data: DeviceCreate) -> None:
   api_client.request("POST", "/devices/", json={"data": data.model_dump()})


# header and etc.
st.header("Inventory")
st.divider()

check_for_password_verification()

# fetching data
with st.status("Fetching Devices...", expanded=True) as status:
    st.write("Get all Devices...")
    devices = fetch_device_fleet()

    status.update(label="Fetching complete", expanded=False, state="complete")

# tabs
tab_list, tab_manage, tab_register = st.tabs([
    "Device Fleet",
    "Actions",
    "Register Device"
])

# device fleet (list and export)
with tab_list:
    st.subheader("Fleet")

    if devices:
        df = pd.DataFrame(devices)
        df["is_active"] = df["is_active"].astype(bool)

        st.dataframe(
            df,
            column_config={
                "name": st.column_config.TextColumn("Name"),
                "location": st.column_config.TextColumn("Location"),
                "status": st.column_config.TextColumn("Status"),
                "is_active": st.column_config.CheckboxColumn("Active"),
                "type": st.column_config.TextColumn("Type"),
                "firmware_version": st.column_config.TextColumn("Firmware Version"),
                "id": None,
                "has_battery": None,
                "created_at": None,
                "modified_at": None
            },
            hide_index=True,
            use_container_width=True
        )

        # csv export
        _, col_exp = st.columns([6, 1])
        with col_exp:
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Export CSV",
                data=csv,
                file_name=f"inventory_{datetime.now().strftime("%Y_%m_%d")}.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.info("No Devices found in the database")

# actions (update and delete)
with tab_manage:
    st.subheader("Management")

    if devices:
        # select box
        device_options = {f"{device["name"]} ({device["location"]})": device for device in devices}
        selected_label = st.selectbox("Select a device to manage", options=list(device_options.keys()))
        selected_device = device_options[selected_label]

        with st.form("edit_device_form"):
            col_edit1, col_edit2 = st.columns(2)

            with col_edit1:
                new_name = st.text_input("Device Name", value=selected_device.get("name", ""), max_chars=20)
                new_loc = st.text_input("Location", value=selected_device.get("location", ""), max_chars=30)
                new_desc = st.text_area("Description", value=selected_device.get("description", ""), height=80, max_chars=200)

            with col_edit2:
                new_firmware = st.text_input("Firmware Version", value=selected_device.get("firmware_version", ""), max_chars=32)
                new_status = st.selectbox(
                    "Status",
                    DeviceStatus.values(),
                    index=DeviceStatus.values().index(selected_device.get("status", "online"))
                )
                new_active = st.toggle("Is Active", value=bool(selected_device.get("is_active", True)),
                                       help="If the device is currently active")

            # save button
            st.space("xsmall")
            if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
                inputs = [new_name, new_loc, new_firmware, new_desc]

                # strip the inputs
                new_name, new_loc, new_firmware, new_desc = [i.strip() if i else i for i in inputs]

                # check for unfilled params
                if not all((new_name, new_loc, new_firmware)):
                    st.error("Oops, any of those params is unfilled: Device Name, Location or Firmware Version")
                    st.stop()

                updates = DeviceUpdate(
                    name=new_name,
                    firmware_version=new_firmware,
                    status=new_status,
                    location=new_loc,
                    is_active=new_active
                )

                result = update_device(updates, selected_device["id"])
                if not isinstance(result, str):
                    st.toast(f"Details for {new_name} updated successfully")

                else:
                    st.info(result)

        # delete device
        st.space("medium")
        with st.expander("Danger Zone", expanded=False):
            st.info("These actions are permanent and cannot be undone")

            col_del1, col_del2 = st.columns([3, 1])
            with col_del1:
                st.write("**Delete Device**")
                st.write(f"Removing {selected_device["name"]} from the registry")

            with col_del2:
                if st.button("Delete", type="secondary", use_container_width=True, key="del_btn"):
                    delete_device(selected_device["id"])
                    st.toast(f"Device {selected_device["name"]} deleted")

    else:
        st.info("No devices available to manage")

# register new device
with tab_register:
    st.subheader("Add new Device")

    with st.form("registration_form"):
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            name = st.text_input("Device Name", max_chars=20)
            dev_type = st.selectbox("Type", DeviceTypes.values())
            loc = st.text_input("Location", max_chars=30)
            desc = st.text_area("Description", max_chars=200, height=80)

        with col_f2:
            firmware = st.text_input("Firmware Version", max_chars=32)
            status = st.selectbox("Status", DeviceStatus.values(), index=DeviceStatus.values().index("online"))
            active = st.toggle(
                "Is Active",
                value=True,
                help="If the Device is currently active"
            )
            battery = st.toggle(
                "Battery",
                value=True,
                help="If the Device has battery"
            )

        st.caption("Only the description is optional")

        if st.form_submit_button("Register Device", type="primary", use_container_width=True):
            inputs = [name, dev_type, loc, desc, firmware]

            # strip the inputs
            name, dev_type, loc, desc, firmware = [i.strip() if i else i for i in inputs]

            # check if all fields are filled
            if not all((name, dev_type, loc, firmware)):
                st.error("Please fill in all required fields")
                st.stop()

            new_device = DeviceCreate(
                name=name,
                type=dev_type,
                firmware_version=firmware,
                status=status,
                location=loc,
                is_active=active,
                has_battery=battery
            )
            register_new_device(new_device)
            st.toast(f"Device '{name}' successfully registered")

# footer
st.divider()
st.caption("S.E.D.M.S - Open Source IoT Management System | [GitHub](https://github.com/Letox74/S.E.D.M.S)")
