import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

def fetch_logo(company_name):
    # Try Clearbit Logo API (returns PNG favicon for many orgs)
    clearbit_url = f"https://logo.clearbit.com/{company_name.replace(' ', '').lower()}.com"
    try:
        response = requests.get(clearbit_url)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except Exception:
        pass
    # Fallback default logo (gray circle)
    logo = Image.new('RGBA', (100,100), (200,200,200,255))
    draw = ImageDraw.Draw(logo)
    draw.ellipse((10, 10, 90, 90), fill=(150,150,150,255))
    return logo

def compose_image(logo, job_title, details):
    # Create blank template
    img = Image.new('RGB', (700, 900), (245, 250, 255))
    draw = ImageDraw.Draw(img)

    # Paste Logo
    logo = logo.resize((110,110))
    img.paste(logo, (295, 30), logo if logo.mode=='RGBA' else None)

    # Fonts
    title_font = ImageFont.truetype("arialbd.ttf", 42)
    detail_font = ImageFont.truetype("arial.ttf", 26)
    big_font = ImageFont.truetype("arialbd.ttf", 33)
    small_font = ImageFont.truetype("arial.ttf", 22)

    y = 160
    draw.text((60, y), job_title, fill=(27,107,221), font=title_font)
    y += 55

    # Draw the rest of the details, line by line
    for section in details.strip().split('\n'):
        if section.startswith('**') and section.endswith('**'):
            draw.text((50, y), section.strip('*'), fill=(224,60,60), font=big_font)
            y += 38
        else:
            draw.text((60, y), section, fill=(72,72,75), font=detail_font)
            y += 35

    # Footer
    draw.rectangle([0,860,700,900], fill=(230,230,230))
    draw.text((40, 870), "🔗 Generated using InstaJobPost (Streamlit Demo)", font=small_font, fill=(44,44,44))

    return img

st.title("Job Post Image Generator")
company = st.text_input("Organization / Company Name", "Indian Army")
job_title = st.text_input("Job Title / Headline", "Indian Army 2025")
details = st.text_area("Job Details (each field on new line)", """Post Name: Indian Army 10+2 TES 54 Exam
Qualification: 12th Pass
Salary: Rs. 56,100/- pm
Age Limit: Minimum Age: 16 Year 6 Month
Selection Process: Application > Shortlisting > SSB > Medical > Merit > Joining Letter
Application Fee: UR/OBC/EWS: ₹ 00/-  PH/SC/ST/PWD: ₹ 00/-
Important Dates: Last Date : 12 June 2025""")

if st.button("Generate Image"):
    logo = fetch_logo(company)
    out_img = compose_image(logo, job_title, details)
    st.image(out_img, caption="Generated Job Post", use_column_width=True)
    # Save and offer download
    buf = BytesIO()
    out_img.save(buf, format="PNG")
    byte_im = buf.getvalue()
    st.download_button('Download PNG', data=byte_im, file_name=f"{company}_JobPost.png", mime="image/png")
