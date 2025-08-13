import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import re

# Load fonts safely with fallback
def load_font(font_path, size):
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()

# Logo fetching with fallback:
# 1) Google Custom Search API (if keys available)
# 2) Clearbit Logo API domain guess
# 3) Default placeholder logo (gray circle)
def fetch_logo_with_fallback(company_name, api_key, cse_id):
    # Try Google Custom Search API if keys present
    if api_key and cse_id:
        try:
            search_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "q": company_name + " logo",
                "cx": cse_id,
                "searchType": "image",
                "num": 1,
                "key": api_key,
                "safe": "active"
            }
            response = requests.get(search_url, params=params, timeout=10)
            data = response.json()
            if "items" in data:
                image_url = data["items"][0]["link"]
                image_response = requests.get(image_url, timeout=10)
                image = Image.open(BytesIO(image_response.content)).convert("RGBA")
                return image
        except Exception:
            pass

    # Fallback to Clearbit Logo API based on domain guess
    try:
        domain_guess = company_name.replace(' ', '').lower() + ".com"
        clearbit_url = f"https://logo.clearbit.com/{domain_guess}"
        response = requests.get(clearbit_url, timeout=5)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception:
        pass

    # Final fallback: default placeholder logo
    logo = Image.new('RGBA', (100, 100), (200, 200, 200, 255))
    draw = ImageDraw.Draw(logo)
    draw.ellipse((10, 10, 90, 90), fill=(150, 150, 150, 255))
    return logo

# Simple AI-powered job details extractor using regex and heuristics
def extract_job_details(text):
    fields = {}

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    # Extract title (first line with job-related keywords)
    for line in lines:
        if len(line) > 5 and any(keyword in line.lower() for keyword in ["recruitment", "job", "vacancy", "position", "post", "hiring"]):
            fields["title"] = line
            break
    else:
        fields["title"] = lines[0] if lines else "Job Opening"

    # Extract vacancies
    vac_match = re.search(r'(\d+)\s+vacancies?', text, re.IGNORECASE)
    if vac_match:
        fields["vacancies"] = vac_match.group(1)

    # Extract age limit
    age_match = re.search(r'age\s*(limit)?[:\s]*([^\n]+)', text, re.IGNORECASE)
    if age_match:
        fields["age_limit"] = age_match.group(2).strip()

    # Extract salary
    salary_match = re.search(r'salary\s*[:\s]*([^\n]+)', text, re.IGNORECASE)
    if salary_match:
        fields["salary"] = salary_match.group(1).strip()

    # Extract eligibility
    elig_match = re.search(r'eligibility\s*[:\s]*([^\n]+)', text, re.IGNORECASE)
    if elig_match:
        fields["eligibility"] = elig_match.group(1).strip()

    # Extract important dates (simple date patterns)
    dates_match = re.findall(r'\b(\d{1,2}[ -/]?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?[ -/]?\d{2,4})\b', text, re.IGNORECASE)
    if dates_match:
        fields["important_dates"] = ', '.join(dates_match)

    return fields

# Helper to draw wrapped multiline text within max width
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
    line_height = font.getbbox('A')[3] - font.getbbox('A')[1] + 6
    for l in lines:
        draw.text((x, y), l.strip(), font=font, fill=fill)
        y += line_height
    return y

# Compose final job post image with logo and extracted details
def compose_image(logo, fields, img_width, img_height):
    background_color = (245, 250, 255)
    img = Image.new('RGB', (img_width, img_height), background_color)
    draw = ImageDraw.Draw(img)

    # Resize and center logo
    logo_size = int(img_width * 0.15)
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
    logo_x = (img_width - logo_size) // 2
    logo_y = 40
    img.paste(logo, (logo_x, logo_y), logo)

    # Load fonts
    title_font = load_font("arialbd.ttf", size=int(img_width * 0.06))
    heading_font = load_font("arialbd.ttf", size=int(img_width * 0.045))
    detail_font = load_font("arial.ttf", size=int(img_width * 0.035))
    small_font = load_font("arial.ttf", size=int(img_width * 0.03))

    y = logo_y + logo_size + 30

    # Draw title centered
    title = fields.get("title", "Job Opening")
    bbox = draw.textbbox((0,0), title, font=title_font)
    w = bbox[2] - bbox[0]
    draw.text(((img_width - w) // 2, y), title, fill=(27,107,221), font=title_font)
    y += bbox[3] - bbox[1] + 40

    # Draw other fields if present
    max_text_width = int(img_width * 0.85)
    for key in ["vacancies", "age_limit", "eligibility", "salary", "important_dates"]:
        if key in fields:
            heading = key.replace('_', ' ').title() + ":"
            value = fields[key]
            y = draw_multiline_text(draw, heading, (40, y), heading_font, (224,60,60), max_text_width)
            y = draw_multiline_text(draw, value, (60, y), detail_font, (72,72,75), max_text_width)
            y += 20

    # Footer with credit
    footer_height = int(img_height * 0.05)
    draw.rectangle([0, img_height - footer_height, img_width, img_height], fill=(230, 230, 230))
    footer_text = "🔗 Generated with AI Job Post Generator"
    bbox = draw.textbbox((0,0), footer_text, font=small_font)
    draw.text((20, img_height - footer_height + (footer_height - (bbox[3]-bbox[1])) // 2), footer_text, fill=(44,44,44), font=small_font)

    return img

# Streamlit UI and logic
st.set_page_config(page_title="AI Job Post Image Generator", layout="centered")
st.title("AI Job Post Image Generator")

with st.form("job_form"):
    text_input = st.text_area("Paste your job post details text here", height=250)
    img_size = st.selectbox("Select Image Size", ("Instagram Post (1080x1080)", "Instagram Story (1080x1920)", "LinkedIn Post (1200x627)"))
    submitted = st.form_submit_button("Generate Image")

# Retrieve API key and CSE ID from Streamlit secrets
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "")
GOOGLE_CSE_ID = st.secrets.get("GOOGLE_CSE_ID", "")

if submitted:
    with st.spinner("Extracting details and generating image..."):
        fields = extract_job_details(text_input)
        company_name = fields.get("title", "Company")

        logo = fetch_logo_with_fallback(company_name, GOOGLE_API_KEY, GOOGLE_CSE_ID)

        size_map = {
            "Instagram Post (1080x1080)": (1080, 1080),
            "Instagram Story (1080x1920)": (1080, 1920),
            "LinkedIn Post (1200x627)": (1200, 627)
        }
        img_width, img_height = size_map[img_size]

        result_img = compose_image(logo, fields, img_width, img_height)
        st.image(result_img, caption="Generated Job Post Image", use_column_width=True)

        buf = BytesIO()
        result_img.save(buf, format="PNG")
        byte_im = buf.getvalue()
        st.download_button(
            label="Download Image",
            data=byte_im,
            file_name=f"{company_name.replace(' ', '_')}_JobPost.png",
            mime="image/png"
        )
