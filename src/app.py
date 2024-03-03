from dataclasses import dataclass

import streamlit as st

from chain import RagChain


@dataclass
class Component:
    query: str = st.session_state.get("query", "")
    chain = RagChain()

    @classmethod
    def title(cls):
        st.title("ナレッジ検索デモ")

    @classmethod
    def subtitle(cls):
        st.text(
            """
                質問について、CSVの内容を踏まえて回答します。
            """
        )

    @classmethod
    def input_inquiry_contents(cls):
        with st.form(key="inquiry_form"):
            query = st.text_area("問い合わせ内容", "問い合わせ内容を入力してください。" if cls.query == "" else cls.query, height=150)
            submit_button = st.form_submit_button("問い合わせ開始")

        if submit_button:
            with st.spinner("回答作成中"):
                response = cls.chain.answer(query)
            st.header("問い合わせ結果")
            st.markdown("- 問い合わせ内容")
            st.write(response["question"])
            st.markdown("- 回答内容")
            st.write(response["answer"])
            for i, document in enumerate(response["context"]):
                with st.expander("検索結果" + str(i + 1)):
                    st.markdown("- 内容")
                    st.write(document.page_content)


# ===UI===
# タイトル
Component.title()
# サブタイトル
Component.subtitle()
# 問い合わせ入力
Component.input_inquiry_contents()
# ======
