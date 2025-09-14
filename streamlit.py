import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="ImageAnalyzer — Demo", layout="centered")

st.title("Анализ изображения за секунды")
st.write("Загрузите фото — мы покажем предпросмотр и сгенерируем отчёт.")


uploaded_file = st.file_uploader("Выберите изображение", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Загруженное изображение", use_column_width=True)

    if st.button("Сгенерировать отчёт"):
        with st.spinner("Идёт анализ изображения…"):
            files = {"file": uploaded_file.getvalue()}
            try:
                res = requests.post(f"{API_BASE}/predict/", files={"file": uploaded_file})
                res.raise_for_status()
                data = res.json()
            except Exception as e:
                st.error(f"Ошибка при анализе: {e}")
                st.stop()

        metrics = data.get("metrics", {})
        st.subheader("Результаты анализа")

        for key, label in [
            ("quality", "Качество"),
            ("sharpness", "Резкость"),
            ("light", "Освещённость"),
            ("details", "Детализация"),
        ]:
            val = int(metrics.get(key, 0))
            st.text(f"{label}: {val}%")
            st.progress(val / 100)

        if "image_base64" in data:
            decoded = base64.b64decode(data["image_base64"])
            st.image(decoded, caption="Результат детекции", use_column_width=True)

        detections = data.get("detections", [])
        if detections:
            st.subheader("Обнаруженные объекты")
            for i, d in enumerate(detections, 1):
                st.markdown(
                    f"**{d.get('class', f'Object {i}')}** "
                    f"(conf: {d.get('confidence', 0):.2f})  "
                    f"{'bbox: ' + str(d.get('bbox')) if 'bbox' in d else ''}"
                )

        st.download_button(
            "Экспорт JSON",
            data=bytes(res.text, "utf-8"),
            file_name="image_report.json",
            mime="application/json",
        )

else:
    st.info("Загрузите изображение, чтобы начать анализ.")
