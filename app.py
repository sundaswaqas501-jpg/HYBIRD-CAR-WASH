import os
import base64
from io import BytesIO
from datetime import date, timedelta

import streamlit as st
import arabic_reshaper
from bidi.algorithm import get_display

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ---------------- PAGE SETTINGS ----------------
st.set_page_config(
    page_title="Hybrid Car Services Coupon",
    page_icon="🚘",
    layout="centered"
)

BLUE = HexColor("#0758A5")
DARK_BLUE = HexColor("#073B8C")
GOLD = HexColor("#E7B943")
DARK = HexColor("#222222")
PALE_BLUE = HexColor("#E8F4FF")

st.markdown("""
<style>
.stApp {
    background: #f5f8fc;
}
.block-container {
    max-width: 900px;
    padding-top: 1.5rem;
}
div[data-testid="stForm"] {
    background: white;
    padding: 1.2rem;
    border-radius: 16px;
    border: 1px solid #dce7f5;
}
div.stDownloadButton > button,
div[data-testid="stFormSubmitButton"] > button {
    background: #0758a5;
    color: white;
    border-radius: 10px;
    border: none;
    font-weight: 700;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)


# ---------------- LOGO AND ARABIC FONT ----------------
logo_path = next(
    (p for p in [
        "logo.jpeg",
        "logo.jpg",
        "logo.jpeg.jpeg",
        "logo.jpg.jpeg"
    ] if os.path.exists(p)),
    ""
)

font_path = "NotoKufiArabic-Regular.ttf"
arabic_font_registered = False

if os.path.exists(font_path):
    try:
        pdfmetrics.registerFont(
            TTFont("ArabicKufi", font_path)
        )
        arabic_font_registered = True
    except Exception:
        pass


# ---------------- ARABIC FUNCTIONS ----------------
def contains_arabic(text):
    return any(
        "\u0600" <= char <= "\u06FF"
        or "\uFB50" <= char <= "\uFDFF"
        or "\uFE70" <= char <= "\uFEFF"
        for char in str(text)
    )


def arabic_text(text):
    """Shape Arabic and prepare right-to-left display."""
    text = str(text)

    if contains_arabic(text):
        text = arabic_reshaper.reshape(text)
        text = get_display(text)

    return text


def escape_html(text):
    text = str(text)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ---------------- APP HEADER ----------------
if logo_path:
    st.image(logo_path, use_container_width=True)
else:
    st.warning(
        "Logo not found. Keep logo.jpeg in the same folder as app.py."
    )

st.caption(
    "Create a customer coupon, preview it, and download it as a PDF."
)

today = date.today()

default_terms = """هذا الكوبون صالح للعميل والمركبة المذكورين فقط.
يُستخدم هذا الكوبون مرة واحدة فقط.
يجب تقديم الكوبون عند زيارة مركز غسيل السيارات.
لا يمكن الجمع بين هذا الكوبون وأي عروض أو خصومات أخرى.
يسري الكوبون حتى تاريخ انتهاء الصلاحية الموضح عليه.
لا يمكن استبدال قيمة الخصم بمبلغ نقدي.
لا يشمل الخصم أي خدمات غير مذكورة في تفاصيل الكوبون.
تخضع جميع الخدمات للتوافر وموافقة إدارة المركز."""


# ---------------- CUSTOMER FORM ----------------
with st.form("coupon_form"):

    st.subheader("Customer Details")

    customer_name = st.text_input(
        "Customer Name",
        placeholder="Enter customer name"
    )

    car_number = st.text_input(
        "Car Number",
        placeholder="e.g. ABC-123"
    )

    col1, col2 = st.columns(2)

    with col1:
        issue_date = st.date_input(
            "Issue Date",
            value=today,
            format="DD/MM/YYYY"
        )

    with col2:
        valid_until = st.date_input(
            "Valid Until",
            value=today + timedelta(days=3),
            format="DD/MM/YYYY"
        )

    st.subheader("Coupon Settings")

    discount_text = st.text_input(
        "Discount Text",
        value="50% OFF"
    )

    eligible_services = st.multiselect(
        "Eligible Services",
        [
            "CAR WASH",
            "OIL CHANGE",
            "INTERIOR CLEANING",
            "EXTERIOR WASH"
        ],
        default=["CAR WASH", "OIL CHANGE"]
    )

    terms = st.text_area(
        "Terms & Conditions",
        value=default_terms,
        height=220
    )

    lucky_draw_text = st.text_input(
        "Lucky Draw Heading",
        value="LUCKY DRAW WINNER — SPECIAL OFFER"
    )

    submitted = st.form_submit_button(
        "Update Coupon Preview"
    )


# ---------------- SAVE FORM DATA ----------------
if submitted or "coupon_data" not in st.session_state:

    st.session_state["coupon_data"] = {
        "customer_name": customer_name.strip() if submitted else "",
        "car_number": car_number.strip() if submitted else "",
        "issue_date": issue_date if submitted else today,
        "valid_until": (
            valid_until if submitted
            else today + timedelta(days=3)
        ),
        "discount_text": (
            discount_text.strip() or "SPECIAL OFFER"
            if submitted else "50% OFF"
        ),
        "eligible_services": (
            eligible_services if submitted
            else ["CAR WASH", "OIL CHANGE"]
        ),
        "terms": terms.strip() if submitted else default_terms,
        "lucky_draw_text": (
            lucky_draw_text.strip()
            if submitted
            else "LUCKY DRAW WINNER — SPECIAL OFFER"
        )
    }


data = st.session_state["coupon_data"]

services_text = (
    ", ".join(data["eligible_services"]) or "None selected"
)

arabic_terms = contains_arabic(data["terms"])

terms_heading = (
    "الشروط والأحكام"
    if arabic_terms
    else "Terms & Conditions"
)


# ---------------- COUPON PREVIEW ----------------
st.divider()
st.subheader("Coupon Preview")

logo_data_uri = ""

if logo_path:
    try:
        with open(logo_path, "rb") as image_file:
            encoded_logo = base64.b64encode(
                image_file.read()
            ).decode("utf-8")

        extension = os.path.splitext(logo_path)[1].lower()
        mime = "image/png" if extension == ".png" else "image/jpeg"

        logo_data_uri = (
            f"data:{mime};base64,{encoded_logo}"
        )
    except Exception:
        pass


preview_terms = escape_html(data["terms"]).replace("\n", "<br>")

if arabic_terms:
    preview_terms = (
        '<div dir="rtl" '
        'style="text-align:right;line-height:2;">'
        + preview_terms +
        '</div>'
    )


st.markdown(f"""
<div style="
    background:white;
    border:3px solid #e7b943;
    border-radius:18px;
    padding:22px;
    color:#222;
">

    <div style="text-align:center;margin-bottom:12px;">
        {
            f'<img src="{logo_data_uri}" '
            'style="width:100%;max-width:480px;'
            'max-height:150px;object-fit:contain;">'
            if logo_data_uri
            else
            '<div style="background:#0758a5;color:white;'
            'padding:15px;font-size:24px;font-weight:800;">'
            'HYBRID CAR SERVICES</div>'
        }
    </div>

    <div style="
        background:#0758a5;
        color:white;
        border-radius:12px;
        padding:12px;
        text-align:center;
    ">
        EXCLUSIVE CUSTOMER DISCOUNT COUPON
    </div>

    <div style="
        font-size:36px;
        font-weight:900;
        color:#0758a5;
        text-align:center;
        margin-top:18px;
    ">
        {escape_html(data["discount_text"])}
    </div>

    <div style="
        font-size:17px;
        font-weight:700;
        color:#0758a5;
        text-align:center;
    ">
        {escape_html(services_text)}
    </div>

    <hr style="border:1px solid #e7b943;">

    <div style="line-height:2;">
        <b>{escape_html(data["lucky_draw_text"])}</b><br>
        <b>Customer Name:</b>
        {escape_html(data["customer_name"] or "________________")}<br>

        <b>Car Number:</b>
        {escape_html(data["car_number"] or "________________")}<br>

        <b>Issue Date:</b>
        {data["issue_date"].strftime("%d %B %Y")}<br>

        <b>Valid Until:</b>
        {data["valid_until"].strftime("%d %B %Y")}<br>

        <b>Eligible Services:</b>
        {escape_html(services_text)}<br>

        <div style="margin-top:12px;">
            <b>{terms_heading}</b>
            {preview_terms}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------- CREATE PDF ----------------
def create_pdf(coupon, image_path):

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4

    # Background and border
    pdf.setFillColor(PALE_BLUE)
    pdf.rect(
        0, 0, page_width, page_height,
        fill=1, stroke=0
    )

    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(4)

    pdf.roundRect(
        28, 28,
        page_width - 56,
        page_height - 56,
        18,
        fill=0,
        stroke=1
    )

    # Logo
    logo_drawn = False

    if image_path and os.path.exists(image_path):
        try:
            pdf.drawImage(
                ImageReader(image_path),
                65,
                page_height - 220,
                width=page_width - 130,
                height=145,
                preserveAspectRatio=True,
                anchor="c",
                mask="auto"
            )
            logo_drawn = True
        except Exception:
            pass

    if not logo_drawn:
        pdf.setFillColor(BLUE)
        pdf.setFont("Helvetica-Bold", 25)
        pdf.drawCentredString(
            page_width / 2,
            page_height - 150,
            "HYBRID CAR SERVICES"
        )

    # Coupon heading
    pdf.setFillColor(DARK_BLUE)
    pdf.setFont("Helvetica-Bold", 14)

    pdf.drawCentredString(
        page_width / 2,
        page_height - 245,
        "EXCLUSIVE CUSTOMER DISCOUNT COUPON"
    )

    # Discount
    pdf.setFillColor(BLUE)
    pdf.setFont("Helvetica-Bold", 34)

    pdf.drawCentredString(
        page_width / 2,
        page_height - 295,
        coupon["discount_text"][:35]
    )

    pdf.setFont("Helvetica-Bold", 10)

    pdf.drawCentredString(
        page_width / 2,
        page_height - 320,
        services_text[:85]
    )

    # Coupon information panel
    panel_x = 48
    panel_y = 105
    panel_w = page_width - 96
    panel_h = page_height - 465

    pdf.setFillColor(white)
    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(2)

    pdf.roundRect(
        panel_x, panel_y,
        panel_w, panel_h,
        12,
        fill=1,
        stroke=1
    )

    y = panel_y + panel_h - 28

    pdf.setFillColor(BLUE)
    pdf.setFont("Helvetica-Bold", 12)

    pdf.drawString(
        panel_x + 18,
        y,
        coupon["lucky_draw_text"][:65]
    )

    y -= 30

    details = [
        ("Customer Name", coupon["customer_name"] or "________________"),
        ("Car Number", coupon["car_number"] or "________________"),
        ("Issue Date", coupon["issue_date"].strftime("%d %B %Y")),
        ("Valid Until", coupon["valid_until"].strftime("%d %B %Y")),
        ("Eligible Services", services_text)
    ]

    pdf.setFillColor(DARK)

    for label, value in details:

        pdf.setFont("Helvetica-Bold", 9.5)
        pdf.drawString(panel_x + 18, y, label + ":")

        pdf.setFont("Helvetica", 9.5)
        pdf.drawString(
            panel_x + 130,
            y,
            str(value)[:60]
        )

        y -= 22

    y -= 5

    # Terms heading
    pdf.setFillColor(HexColor("#555555"))

    if arabic_terms and arabic_font_registered:

        pdf.setFont("ArabicKufi", 10)

        pdf.drawRightString(
            panel_x + panel_w - 18,
            y,
            arabic_text("الشروط والأحكام")
        )

    else:
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(
            panel_x + 18,
            y,
            "Terms & Conditions"
        )

    y -= 20

    # Terms content
    if arabic_terms and not arabic_font_registered:

        pdf.setFont("Helvetica", 9)
        pdf.drawString(
            panel_x + 18,
            y,
            "Arabic font missing. Check the font file."
        )

    else:

        font_name = (
            "ArabicKufi"
            if arabic_terms
            else "Helvetica"
        )

        font_size = 9 if arabic_terms else 8.5

        pdf.setFont(font_name, font_size)

        max_width = panel_w - 36

        # Keep each entered paragraph together as text.
        paragraphs = (coupon["terms"] or "").splitlines()

        for paragraph in paragraphs:

            if not paragraph.strip():
                y -= 6
                continue

            if arabic_terms:
                rendered = arabic_text(paragraph)

                # Arabic paragraph is drawn as one right-aligned line.
                # Keep terms concise enough to fit the panel.
                while (
                    pdfmetrics.stringWidth(
                        rendered, font_name, font_size
                    ) > max_width
                    and len(paragraph) > 10
                ):
                    # Split at word boundaries, preserving Arabic order.
                    words = paragraph.split()
                    if len(words) <= 1:
                        break

                    line_words = []
                    remaining_words = words[:]

                    while remaining_words:
                        test_words = line_words + [remaining_words[0]]
                        test_text = arabic_text(" ".join(test_words))

                        if (
                            pdfmetrics.stringWidth(
                                test_text, font_name, font_size
                            ) <= max_width
                        ):
                            line_words.append(remaining_words.pop(0))
                        else:
                            break

                    if not line_words:
                        line_words = [remaining_words.pop(0)]

                    line = " ".join(line_words)

                    pdf.drawRightString(
                        panel_x + panel_w - 18,
                        y,
                        arabic_text(line)
                    )

                    y -= 15
                    paragraph = " ".join(remaining_words)

                    if not paragraph:
                        break

                    rendered = arabic_text(paragraph)

                if paragraph:
                    pdf.drawRightString(
                        panel_x + panel_w - 18,
                        y,
                        arabic_text(paragraph)
                    )
                    y -= 15

            else:
                pdf.drawString(
                    panel_x + 18,
                    y,
                    paragraph[:95]
                )
                y -= 14

            if y < panel_y + 25:
                break

    # Footer
    pdf.setFillColor(BLUE)
    pdf.setFont("Helvetica-Bold", 9)

    pdf.drawCentredString(
        page_width / 2,
        65,
        "Thank you for choosing Hybrid Car Services!"
    )

    pdf.save()
    buffer.seek(0)

    return buffer.getvalue()


# ---------------- DOWNLOAD BUTTON ----------------
pdf_bytes = create_pdf(data, logo_path)

safe_name = "".join(
    char for char in data["customer_name"]
    if char.isalnum() or char in (" ", "-", "_")
).strip()

filename = (
    "Hybrid_Car_Coupon_"
    + (safe_name.replace(" ", "_") or "Customer")
    + ".pdf"
)

st.download_button(
    "Download Coupon as PDF",
    data=pdf_bytes,
    file_name=filename,
    mime="application/pdf",
    use_container_width=True
)

if not arabic_font_registered:
    st.warning(
        "Arabic font not found. Keep "
        "NotoKufiArabic-Regular.ttf beside app.py."
    )
