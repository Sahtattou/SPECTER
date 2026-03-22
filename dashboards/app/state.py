from __future__ import annotations

import time
from typing import Any

st = __import__("streamlit")


REFRESH_ERROR_COUNT = "refresh_error_count"
LAST_REFRESH_SUCCESS_AT = "last_refresh_success_at"


def bootstrap_state() -> None:
    if REFRESH_ERROR_COUNT not in st.session_state:
        st.session_state[REFRESH_ERROR_COUNT] = 0
    if LAST_REFRESH_SUCCESS_AT not in st.session_state:
        st.session_state[LAST_REFRESH_SUCCESS_AT] = "never"


def mark_refresh_success() -> None:
    st.session_state[LAST_REFRESH_SUCCESS_AT] = time.strftime(
        "%H:%M:%S UTC", time.gmtime()
    )
    st.session_state[REFRESH_ERROR_COUNT] = 0


def bump_refresh_errors() -> None:
    st.session_state[REFRESH_ERROR_COUNT] = (
        int(st.session_state.get(REFRESH_ERROR_COUNT, 0)) + 1
    )


def get_refresh_error_count() -> int:
    return int(st.session_state.get(REFRESH_ERROR_COUNT, 0))


def get_last_refresh_success_at() -> Any:
    return st.session_state.get(LAST_REFRESH_SUCCESS_AT, "never")
