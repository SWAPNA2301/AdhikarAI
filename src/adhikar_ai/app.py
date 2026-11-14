"""Streamlit entry point for the Phase 1 application."""

import streamlit as st


def main() -> None:
    """Render the introductory page and future search placeholder."""
    st.set_page_config(page_title="AdhikarAI", page_icon="🇮🇳")
    st.title("AdhikarAI — Government Scheme Discovery")
    st.write(
        "AdhikarAI aims to help people discover government schemes and "
        "understand their published requirements. This Phase 1 prototype "
        "establishes the application foundation."
    )
    st.info(
        "Scheme search is coming in a future phase. No scheme data is loaded, "
        "and this prototype does not assess eligibility or provide results."
    )
    st.text_input("Search government schemes", placeholder="Coming soon", disabled=True)
    st.button("Search (coming soon)", disabled=True)


if __name__ == "__main__":
    main()
