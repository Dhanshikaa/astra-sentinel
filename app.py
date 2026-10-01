import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from database import init_db, get_articles, upsert_article
from services.data_loader import load_starter_data
from services.ai_processor import process_article


# ---------------------------------------------------------
# SETUP
# ---------------------------------------------------------

load_dotenv()
init_db()

st.set_page_config(
    page_title="ASTRA SENTINEL",
    page_icon="🛰️",
    layout="wide"
)


# ---------------------------------------------------------
# CUSTOM STYLING
# ---------------------------------------------------------

st.markdown("""
<style>
.main-title {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: .04em;
}

.subtitle {
    color: #8b95a7;
    margin-bottom: 1rem;
}

.card {
    padding: 1rem;
    border: 1px solid #303746;
    border-radius: 12px;
    background: #111827;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.markdown(
    '<div class="main-title">🛰️ ASTRA SENTINEL</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">AI-Powered Defence Information Monitoring System</div>',
    unsafe_allow_html=True
)


# ---------------------------------------------------------
# LOAD ARTICLES
# ---------------------------------------------------------

rows = get_articles()


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:

    st.header("Control Panel")

    if st.button(
        "Load ASTRA Starter Dataset",
        use_container_width=True
    ):
        n = load_starter_data()
        st.success(f"Loaded {n} starter articles.")
        st.rerun()

    # API status
    if not os.getenv("OPENAI_API_KEY"):
        st.info(
            "Offline processing mode enabled. "
            "Add an OpenAI API key later to enable LLM processing."
        )
    else:
        st.success("OpenAI AI processing enabled.")

    st.divider()

    page = st.radio(
        "Navigate",
        [
            "Dashboard",
            "Add Article",
            "Intelligence Brief"
        ]
    )


# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":

    df = pd.DataFrame(
        rows,
        columns=[
            "id",
            "title",
            "date",
            "source",
            "url",
            "content",
            "category",
            "summary",
            "keywords",
            "topics",
            "entities",
            "created_at"
        ]
    )

    # No articles
    if df.empty:

        st.info(
            "Load the starter dataset to begin."
        )

        st.stop()

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Articles",
        len(df)
    )

    c2.metric(
        "Processed",
        int(
            (df.summary.fillna("") != "").sum()
        )
    )

    c3.metric(
        "Categories",
        df.category.replace("", pd.NA).nunique()
    )

    # -----------------------------------------------------
    # FILTERS
    # -----------------------------------------------------

    f1, f2, f3 = st.columns(3)

    search = f1.text_input(
        "Search",
        placeholder="title, source, keyword..."
    )

    cats = [
        x
        for x in sorted(df.category.dropna().unique())
        if x
    ]

    category = f2.selectbox(
        "Category",
        ["All"] + cats
    )

    dates = sorted(
        df.date.dropna().unique(),
        reverse=True
    )

    date = f3.selectbox(
        "Date",
        ["All"] + list(dates)
    )

    # -----------------------------------------------------
    # APPLY FILTERS
    # -----------------------------------------------------

    view = df.copy()

    if search:

        mask = view.astype(str).apply(
            lambda col: col.str.contains(
                search,
                case=False,
                na=False
            )
        ).any(axis=1)

        view = view[mask]

    if category != "All":

        view = view[
            view.category == category
        ]

    if date != "All":

        view = view[
            view.date == date
        ]

    st.caption(
        f"Showing {len(view)} article(s)"
    )

    # -----------------------------------------------------
    # PROCESS ALL UNPROCESSED ARTICLES
    # -----------------------------------------------------

    if st.button("Process All Unprocessed Articles"):

        rows = [
            r for r in get_articles()
            if not r[7]
        ]

        if not rows:

            st.info(
                "All articles are already processed."
            )

        else:

            progress = st.progress(0)
            status = st.empty()

            for i, r in enumerate(rows, start=1):

                status.write(
                    f"Processing {i}/{len(rows)}: {r[1]}"
                )

                try:

                    result = process_article(
                        r[1],
                        r[5]
                    )

                    upsert_article(
                        {
                            "id": r[0],
                            "title": r[1],
                            "date": r[2],
                            "source": r[3],
                            "url": r[4],
                            "content": r[5],
                            "category": result["category"],
                            "summary": result["summary"],
                            "keywords": ", ".join(
                                result["keywords"]
                            ),
                            "topics": ", ".join(
                                result["topics"]
                            ),
                            "entities": ", ".join(
                                result["entities"]
                            )
                        }
                    )

                except Exception as e:

                    st.error(
                        f"Failed to process {r[1]}: {e}"
                    )

                progress.progress(
                    i / len(rows)
                )

            status.success(
                "All available articles processed."
            )

            st.rerun()

    # -----------------------------------------------------
    # ARTICLE CARDS
    # -----------------------------------------------------

    for _, r in view.iterrows():

        with st.container(border=True):

            top = st.columns([6, 2, 2])

            top[0].markdown(
                f"### {r.title}"
            )

            top[1].write(
                r.category or "Not processed"
            )

            top[2].write(
                r.date
            )

            st.write(
                r.summary or "Not processed yet."
            )

            if r.keywords:

                st.caption(
                    "Keywords: " + r.keywords
                )

            if r.topics:

                st.caption(
                    "Topics: " + r.topics
                )

            if r.entities:

                st.caption(
                    "Entities: " + r.entities
                )

            if r.source:

                st.caption(
                    f"Source: {r.source}"
                )

            if r.url:

                st.link_button(
                    "Open source",
                    r.url
                )

            if not r.summary:

                if st.button(
                    "Process Article",
                    key=f"p_{r.id}"
                ):

                    try:

                        result = process_article(
                            r.title,
                            r.content
                        )

                        upsert_article(
                            {
                                "id": r.id,
                                "title": r.title,
                                "date": r.date,
                                "source": r.source,
                                "url": r.url,
                                "content": r.content,
                                "category": result["category"],
                                "summary": result["summary"],
                                "keywords": ", ".join(
                                    result["keywords"]
                                ),
                                "topics": ", ".join(
                                    result["topics"]
                                ),
                                "entities": ", ".join(
                                    result["entities"]
                                )
                            }
                        )

                        st.success(
                            "Article processed successfully."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Article processing failed: {e}"
                        )    


# =========================================================
# ADD ARTICLE
# =========================================================

elif page == "Add Article":

    st.header("Add New Article")

    with st.form("add"):

        title = st.text_input(
            "Title"
        )

        date = st.date_input(
            "Date"
        )

        source = st.text_input(
            "Source"
        )

        url = st.text_input(
            "Source URL"
        )

        content = st.text_area(
            "Article content",
            height=260
        )

        submitted = st.form_submit_button(
            "Add & Process Article"
        )

    if submitted:

        # Validate input
        if not title.strip():

            st.error(
                "Title is required."
            )

        elif not content.strip():

            st.error(
                "Article content is required."
            )

        else:

            try:

                result = process_article(
                    title,
                    content
                )

                import hashlib

                article_id = (
                    "custom-"
                    + hashlib.sha1(
                        title.encode()
                    ).hexdigest()[:10]
                )

                upsert_article(
                    {
                        "id": article_id,
                        "title": title,
                        "date": str(date),
                        "source": source,
                        "url": url,
                        "content": content,
                        "category": result["category"],
                        "summary": result["summary"],
                        "keywords": ", ".join(
                            result["keywords"]
                        ),
                        "topics": ", ".join(
                            result["topics"]
                        ),
                        "entities": ", ".join(
                            result["entities"]
                        )
                    }
                )

                st.success(
                    "Article added and processed successfully."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Could not process article: {e}"
                )


# =========================================================
# INTELLIGENCE BRIEF
# =========================================================

else:

    st.header(
        "ASTRA Intelligence Brief"
    )

    st.write(
        "Generate a concise brief from the articles "
        "currently stored in SENTINEL."
    )

    question = st.text_input(
        "Ask a question",
        placeholder=(
            "What are the main technology themes "
            "in the collection?"
        )
    )

    if st.button(
        "Generate Brief"
    ):

        if not question.strip():

            st.error(
                "Enter a question first."
            )

        elif not os.getenv("OPENAI_API_KEY"):

            st.warning(
                "Intelligence Brief currently requires "
                "an OpenAI API key."
            )

        else:

            rows = get_articles()

            context = "\n\n".join(
                [
                    f"TITLE: {r[1]}\n"
                    f"DATE: {r[2]}\n"
                    f"SOURCE: {r[3]}\n"
                    f"SUMMARY: {r[7]}"
                    for r in rows
                    if r[7]
                ]
            )

            if not context:

                st.warning(
                    "Process some articles first."
                )
            else:

                processed = [
                    r for r in rows
                    if r[7]
                ]

                st.markdown("### ASTRA Intelligence Brief")

                st.write(
                    f"Based on {len(processed)} processed articles currently "
                    "stored in SENTINEL:"
                )

                for r in processed[:8]:

                    st.markdown(
                        f"**{r[1]}**"
                    )

                    st.write(
                        r[7]
                    )

                    st.caption(
                        f"{r[2]} · {r[3]}"
                    )

                st.success(
                    "Brief generated from the processed SENTINEL intelligence collection."
                )