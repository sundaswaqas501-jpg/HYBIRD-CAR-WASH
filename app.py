import os
import base64
from io import BytesIO
from datetime import date, timedelta

import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader

st.set_page_config(page_title="Hybrid Car Services Coupon", page_icon="🚘", layout="centered")

BLUE = HexColor("#0758A5")
DARK_BLUE = HexColor("#073B8C")
PALE_BLUE = HexColor("#E8F4FF")
GOLD = HexColor("#E7B943")
DARK = HexColor("#222222")

st.markdown("""
<style>
.stApp { background: #f5f8fc; }
.block-container { max-width: 900px; padding-top: 1.5rem; }
div[data-testid="stForm"] { background: white; padding: 1.2rem; border-radius: 16px; border: 1px solid #dce7f5; }
div.stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button { background: #0758a5; color: white; border-radius: 10px; border: none; font-weight: 700; width: 100%; }
</style>
""", unsafe_allow_html=True)

# Keep logo.jpeg in the same folder as app.py.
logo_path = next((p for p in ("logo.jpeg", "logo.jpg", "logo.jpeg.jpeg", "logo.jpg.jpeg") if os.path.exists(p)), "")
if logo_path:
    st.image(logo_path, use_container_width=True)
else:
    st.warning("Logo not found. Put logo.jpeg in the same folder as app.py.")

st.caption("Create a customer coupon, preview it, and download it as a PDF.")
today = date.today()

with st.form("coupon_form"):
    st.subheader("Customer Details")
    customer_name = st.text_input("Customer Name", placeholder="Enter customer name")
    car_number = st.text_input("Car Number", placeholder="e.g. ABC-123")
    col1, col2 = st.columns(2)
    with col1:
        issue_date = st.date_input("Issue Date", value=today, format="DD/MM/YYYY")
    with col2:
        valid_until = st.date_input("Valid Until", value=today + timedelta(days=3), format="DD/MM/YYYY")

    st.subheader("Coupon Settings")
    discount_text = st.text_input("Discount Text", value="50% OFF")
    eligible_services = st.multiselect(
        "Eligible Services",
        ["CAR WASH", "OIL CHANGE", "INTERIOR CLEANING", "EXTERIOR WASH"],
        default=["CAR WASH", "OIL CHANGE"],
    )
    terms = st.text_area(
        "Terms & Conditions",
        value="Valid for the named customer and vehicle. One-time use only. Cannot be combined with other offers.",
        height=90,
    )
    lucky_draw_text = st.text_input("Lucky Draw Heading", value="LUCKY DRAW WINNER — SPECIAL OFFER")
    submitted = st.form_submit_button("Update Coupon Preview")

if submitted or "coupon_data" not in st.session_state:
    st.session_state["coupon_data"] = {
        "customer_name": customer_name.strip() if submitted else "",
        "car_number": car_number.strip() if submitted else "",
        "issue_date": issue_date if submitted else today,
        "valid_until": valid_until if submitted else today + timedelta(days=3),
        "discount_text": (discount_text.strip() or "SPECIAL OFFER") if submitted else "50% OFF",
        "eligible_services": eligible_services if submitted else ["CAR WASH", "OIL CHANGE"],
        "terms": terms.strip() if submitted else "Valid for the named customer and vehicle. One-time use only. Cannot be combined with other offers.",
        "lucky_draw_text": lucky_draw_text.strip() if submitted else "LUCKY DRAW WINNER — SPECIAL OFFER",
    }

data = st.session_state["coupon_data"]
services_text = ", ".join(data["eligible_services"]) or "None selected"

def esc(value):
    return (str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

st.divider()
st.subheader("Coupon Preview")
logo_data_uri = ""
if logo_path:
    try:
        with open(logo_path, "rb") as logo_file:
            encoded_logo = base64.b64encode(logo_file.read()).decode("utf-8")
        ext = os.path.splitext(logo_path)[1].lower()
        mime = "image/png" if ext == ".png" else "image/jpeg"
        logo_data_uri = f"data:{mime};base64,{encoded_logo}"
    except OSError:
        logo_data_uri = ""

st.markdown(f"""
<div style="background:white;border:3px solid #e7b943;border-radius:18px;padding:22px;color:#222;">
  <div style="text-align:center;margin-bottom:12px;">
    {f'<img src="{logo_data_uri}" style="width:100%;max-width:480px;max-height:150px;object-fit:contain;border-radius:8px;" />' if logo_data_uri else '<div style="background:#0758a5;color:white;border-radius:12px;padding:15px;font-size:24px;font-weight:800;">HYBRID CAR SERVICES</div>'}
  </div>
  <div style="background:#0758a5;color:white;border-radius:12px;padding:12px;text-align:center;">
    <div style="font-size:13px;">EXCLUSIVE CUSTOMER DISCOUNT COUPON</div>
  </div>
  <div style="font-size:36px;font-weight:900;color:#0758a5;text-align:center;margin-top:18px;">{esc(data['discount_text'])}</div>
  <div style="font-size:17px;font-weight:700;color:#0758a5;text-align:center;">{esc(services_text)}</div>
  <hr style="border:1px solid #e7b943;">
  <div style="line-height:2;">
    <b>{esc(data['lucky_draw_text'])}</b><br>
    <b>Customer Name:</b> {esc(data['customer_name'] or '________________')}<br>
    <b>Car Number:</b> {esc(data['car_number'] or '________________')}<br>
    <b>Issue Date:</b> {data['issue_date'].strftime('%d %B %Y')}<br>
    <b>Valid Until:</b> {data['valid_until'].strftime('%d %B %Y')}<br>
    <b>Eligible Services:</b> {esc(services_text)}<br>
    <small><b>Terms &amp; Conditions:</b> {esc(data['terms'])}</small>
  </div>
</div>
""", unsafe_allow_html=True)

def create_pdf(coupon, image_file):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4

    pdf.setFillColor(PALE_BLUE)
    pdf.rect(0, 0, page_width, page_height, fill=1, stroke=0)
    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(4)
    pdf.roundRect(28, 28, page_width - 56, page_height - 56, 18, fill=0, stroke=1)

    # Logo replaces the separate business-name heading in the PDF.
    logo_drawn = False
    if image_file and os.path.exists(image_file):
        try:
            pdf.drawImage(ImageReader(image_file), 65, page_height - 245,
                          width=page_width - 130, height=165,
                          preserveAspectRatio=True, anchor="c", mask="auto")
            logo_drawn = True
        except Exception:
            pass
    if not logo_drawn:
        pdf.setFillColor(BLUE)
        pdf.setFont("Helvetica-Bold", 25)
        pdf.drawCentredString(page_width / 2, page_height - 150, "HYBRID CAR SERVICES")

    pdf.setFillColor(DARK_BLUE)
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawCentredString(page_width / 2, page_height - 270, "EXCLUSIVE CUSTOMER DISCOUNT COUPON")
    pdf.setFillColor(BLUE)
    pdf.setFont("Helvetica-Bold", 38)
    pdf.drawCentredString(page_width / 2, page_height - 330, coupon["discount_text"][:35])
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawCentredString(page_width / 2, page_height - 360, services_text[:85])

    panel_x, panel_y = 55, 155
    panel_w, panel_h = page_width - 110, page_height - 565
    pdf.setFillColor(white)
    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(2)
    pdf.roundRect(panel_x, panel_y, panel_w, panel_h, 12, fill=1, stroke=1)

    y = panel_y + panel_h - 32
    pdf.setFillColor(BLUE)
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(panel_x + 20, y, coupon["lucky_draw_text"][:65])
    y -= 35
    details = [
        ("Customer Name", coupon["customer_name"] or "________________"),
        ("Car Number", coupon["car_number"] or "________________"),
        ("Issue Date", coupon["issue_date"].strftime("%d %B %Y")),
        ("Valid Until", coupon["valid_until"].strftime("%d %B %Y")),
        ("Eligible Services", services_text),
    ]
    pdf.setFillColor(DARK)
    for label, value in details:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(panel_x + 20, y, label + ":")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(panel_x + 135, y, value[:60])
        y -= 25

    y -= 5
    pdf.setFillColor(HexColor("#555555"))
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(panel_x + 20, y, "Terms & Conditions:")
    y -= 16
    pdf.setFont("Helvetica", 8)
    line = ""
    for word in (coupon["terms"] or "No additional terms.").split():
        if len(line + " " + word) > 82:
            pdf.drawString(panel_x + 20, y, line)
            y -= 12
            line = word
            if y < panel_y + 15:
                break
        else:
            line = (line + " " + word).strip()
    if line and y >= panel_y + 15:
        pdf.drawString(panel_x + 20, y, line)

    pdf.setFillColor(BLUE)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(page_width / 2, 85, "Thank you for choosing Hybrid Car Services!")
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()

pdf_bytes = create_pdf(data, logo_path)
safe_name = "".join(ch for ch in data["customer_name"] if ch.isalnum() or ch in (" ", "-", "_")).strip()
filename = f"Hybrid_Car_Coupon_{safe_name.replace(' ', '_') or 'Customer'}.pdf"
st.download_button("Download Coupon as PDF", data=pdf_bytes, file_name=filename,
                   mime="application/pdf", use_container_width=True)
