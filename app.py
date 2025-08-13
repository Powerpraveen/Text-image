import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# Safe font loader with fallback
def load_font(font_path, size):
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()

# Fetch logo image from Clearbit API or fallback placeholder
def fetch_logo(company_name):
    clearbit_url = f"https://logo.clearbit.com/{company_name.replace(' ', '').lower()}.com"
    try:
        response = requests.get(clearbit_url, timeout=5)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception:
        pass
    # Fallback: gray circle logo
    logo = Image.new('RGBA', (100, 100), (200, 200, 200, 255))
    draw = ImageDraw.Draw(logo)
    draw.ellipse((10, 10, 90, 90), fill=(150, 150, 150, 255))
    return logo

# Text wrapping helper: draws multiline text within max width
def draw_multiline_text(draw, text, position, font, fill, max_width):
    words = text.split(' ')
    lines = []
    line = ''
    for word in words:
        test_line = line + word + ' '
        bbox = draw.textbbox((0,0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word + ' '
    lines.append(line)

    x, y = position
    line_height = font.getbbox('A')[3] - font.getbbox('A')[1] + 4
    for l in lines:
        draw.text((x, y), l.strip(), font=font, fill=fill)
        y += line_height
    return y

# Compose the final image with logo, title, and details
def compose_image(logo, job_title, details, img_width, img_height):
    background_color = (245, 250, 255)
    img = Image.new('RGB', (img_width, img_height), background_color)
    draw = ImageDraw.Draw(img)

    # Resize and center logo
    logo_size = int(img_width * 0.15)
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
    logo_x = (img_width - logo_size) // 2
    logo_y = 30
    img.paste(logo, (logo_x, logo_y), logo)

    # Load fonts (replace with your .ttf files if available)
    title_font = load_font("arialbd.ttf", size=int(img_width * 0.06))
    big_font = load_font("arialbd.ttf", size=int(img_width * 0.045))
    detail_font = load_font("arial.ttf", size=int(img_width * 0.035))
    small_font = load_font("arial.ttf", size=int(img_width * 0.03))

    # Draw job title centered below logo
    bbox = draw.textbbox((0, 0), job_title, font=title_font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    y = logo_y + logo_size + 20
    draw.text(((img_width - w) // 2, y), job_title, fill=(27, 107, 221), font=title_font)
    y += h + 25

    # Draw each line of job details with styling and wrapping
    max_text_width = int(img_width * 0.85)
    lines = details.strip().split('\n')

    for line in lines:
        line = line.strip()
        if line.startswith('**') and line.endswith('**'):
            # Bold red heading
            clean_text = line.strip('*').strip()
            y = draw_multiline_text(draw, clean_text, (40, y), big_font, (224, 60, 60), max_text_width)
            y += 10
        else:
            # Normal detail text
            y = draw_multiline_text(draw, line, (40, y), detail_font, (72, 72, 75), max_text_width)
            y += 8

    # Footer bar with credit text
    footer_height = int(img_height * 0.05)
    draw.rectangle([0, img_height - footer_height, img_width, img_height], fill=(230, 230, 230))
    footer_text = "🔗 Generated with InstaJobPost (Streamlit Demo)"
    bbox = draw.textbbox((0, 0), footer_text, font=small_font)
    fw = bbox[2] - bbox[0]
    fh = bbox[3] - bbox[1]
    draw.text((20, img_height - footer_height + (footer_height - fh) // 2), footer_text, fill=(44, 44, 44), font=small_font)

    return img

# Streamlit app starts here
st.set_page_config(page_title="Job Post Image Generator", layout="centered")

st.title("Job Post Image Generator")

company = st.text_input("Organization / Company Name", "Indian Army")
job_title = st.text_input("Job Title / Headline", "Indian Army 2025")
details = st.text_area("Job Details (each field on new line)", """**BEL Recruitment 2025 – Vacancy Details**
**Management Industrial Trainees (Finance)**
Age limit
Maximum Age: 25 years
Job Details
904 vacancies
Eligibility
ICWA (Inter) or CA (Inter)
Salary
₹30,000.
Last date for submission of application
📅Walk-in Interview: 19-Aug-2025""")

size_options = {
    "Instagram Post (1080x1080)": (1080, 1080),
    "Instagram Story (1080x1920)": (1080, 1920),
    "LinkedIn Post (1200x627)": (1200, 627),
    "Twitter Post (1024x512)": (1024, 512)
}

size_choice = st.selectbox("Select Image Size", options=list(size_options.keys()))
img_width, img_height = size_options[size_choice]

if st.button("Generate Image"):
    with st.spinner("Generating image..."):
        logo = fetch_logo(company)
        out_img = compose_image(logo, job_title, details, img_width, img_height)
        st.image(out_img, caption="Generated Job Post", use_column_width=True)

        buf = BytesIO()
        out_img.save(buf, format="PNG")
        byte_im = buf.getvalue()

        st.download_button(
            label="Download PNG",
            data=byte_im,
            file_name=f"{company.replace(' ', '_')}_JobPost.png",
            mime="image/png"
        )
