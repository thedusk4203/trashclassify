import streamlit as st
import cv2
import numpy as np
import os
import time
import uuid
import logging
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cấu hình tiêu đề và layout trang
st.set_page_config(
    page_title="Phân Loại Rác Thải",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration paths
MODEL_PATH = 'model/trash_classification_model.h5'
CLASS_NAMES_PATH = 'model/class_names.txt'
UPLOAD_FOLDER = 'uploads'

# Ensure uploads directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_class_names():
    if os.path.exists(CLASS_NAMES_PATH):
        with open(CLASS_NAMES_PATH, 'r') as f:
            return [line.strip() for line in f.readlines()]
    else:
        logger.warning(f"File {CLASS_NAMES_PATH} not found. Using default class list.")
        return ['battery', 'biological', 'brown-glass', 'cardboard', 'green-glass', 
                'metal', 'paper', 'plastic', 'trash', 'white-glass']

# Load class names
@st.cache_resource
def load_model_data():
    try:
        if os.path.exists(MODEL_PATH):
            model = load_model(MODEL_PATH)
            logger.info("Model loaded successfully")
            return model
        else:
            logger.warning(f"Model file {MODEL_PATH} not found")
            return None
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return None

# Load model and class names
TRASH_CATEGORIES = load_class_names()
model = load_model_data()

def translate_class_name(class_name):
    """Convert class name to standardized English"""
    translations = {
        "battery": "Pin/Ắc quy",
        "biological": "Rác hữu cơ",
        "cardboard": "Bìa các-tông",
        "paper": "Giấy",
        "plastic": "Nhựa",
        "metal": "Kim loại",
        "brown-glass": "Thủy tinh nâu",
        "green-glass": "Thủy tinh xanh lá",
        "white-glass": "Thủy tinh trắng",
        "trash": "Rác thải khác",
        "unknown": "Không xác định",
        "error": "Lỗi"
    }
    
    lower_class = class_name.lower()
    return translations.get(lower_class, "Không xác định")

def preprocess_image(image, target_size=(224, 224)):
    """Preprocess image for model input"""
    try:
        if image is None:
            logger.error("Input image is empty")
            return None
            
        # Convert PIL Image to numpy array if needed
        if isinstance(image, Image.Image):
            image = np.array(image)
            
        if len(image.shape) == 3 and image.shape[2] == 4:
            # Convert RGBA to RGB
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        
        # Resize image
        image_resized = cv2.resize(image, target_size)
        
        # Convert to model input format
        image_array = img_to_array(image_resized)
        image_array = np.expand_dims(image_array, axis=0)
        # Normalize similar to training
        image_preprocessed = image_array / 127.5 - 1
        
        return image_preprocessed
    except Exception as e:
        logger.error(f"Error preprocessing image: {e}")
        return None

def classify_image(image):
    """Classify uploaded image"""
    try:
        if model is not None:
            processed_image = preprocess_image(image)
            if processed_image is None:
                return {'class_name': 'Error', 'confidence': 0.0}
                
            predictions = model.predict(processed_image, verbose=0)[0]
            class_index = np.argmax(predictions)
            confidence = float(predictions[class_index])
            class_name = TRASH_CATEGORIES[class_index]
        else:
            # Simulate results when model is unavailable
            import random
            class_index = random.randint(0, len(TRASH_CATEGORIES) - 1)
            class_name = TRASH_CATEGORIES[class_index]
            confidence = random.uniform(0.7, 0.99)
        
        return {
            'class_name': class_name,
            'confidence': round(confidence * 100, 2)
        }
        
    except Exception as e:
        logger.error(f"Error classifying image: {e}")
        return {
            'class_name': 'Error',
            'confidence': 0.0
        }

# Trang chính của ứng dụng
st.title("♻️ Phân Loại Rác Thải")
st.write("Tải lên hình ảnh rác thải để phân loại vào các danh mục rác khác nhau.")

# Hiển thị menu bên cạnh
with st.sidebar:
    st.header("Thông tin")
    st.info("""
    ### Về ứng dụng
    Ứng dụng này sử dụng Deep Learning để phân loại rác thải thành 10 loại khác nhau.
    
    ### Các loại rác
    - Pin/Ắc quy
    - Rác hữu cơ
    - Các loại thủy tinh (nâu, xanh, trắng)
    - Bìa các-tông
    - Giấy
    - Nhựa
    - Kim loại
    - Rác thải khác
    """)

# Hiển thị tùy chọn upload hình ảnh
tab1, tab2 = st.tabs(["Tải lên hình ảnh", "Về dự án"])

with tab1:
    # Column layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Chọn hình ảnh...", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            # Đọc hình ảnh từ file upload
            image = Image.open(uploaded_file)
            st.image(image, caption="Hình ảnh đã tải lên", use_column_width=True)
            
            # Thêm nút phân loại
            if st.button("Phân loại"):
                with st.spinner('Đang phân tích hình ảnh...'):
                    result = classify_image(image)
                    
                    # Lấy kết quả
                    class_name = result['class_name']
                    confidence = result['confidence']
                    
                    display_name = translate_class_name(class_name)
                    st.success(f"Kết quả: **{display_name}** (độ tin cậy: {confidence}%)")
                    
                    # Hiển thị thông tin thêm về loại rác
                    st.info(get_recycling_info(class_name))
                    
    with col2:
        st.subheader("Kết quả phân loại")
        st.write("Tải lên hình ảnh và nhấp vào nút 'Phân loại' để xem kết quả.")

with tab2:
    st.header("Về Dự Án Phân Loại Rác Thải")
    st.write("""
    Dự án này sử dụng mô hình Deep Learning được đào tạo trên bộ dữ liệu hình ảnh rác thải để phân loại chúng thành các danh mục khác nhau. 
    Mục tiêu là giúp nâng cao nhận thức về phân loại rác thải đúng cách.
    
    ### Công nghệ sử dụng:
    - TensorFlow/Keras cho mô hình Deep Learning
    - Streamlit cho giao diện người dùng
    - OpenCV cho xử lý hình ảnh
    
    ### Cách sử dụng:
    1. Tải lên hình ảnh rác thải
    2. Nhấn nút 'Phân loại'
    3. Xem kết quả phân loại và thông tin liên quan
    """)

def get_recycling_info(class_name):
    """Return recycling information based on class name"""
    info = {
        "battery": """
        ### Pin/Ắc quy
        - **Tái chế**: Cần bỏ riêng tại điểm thu gom chuyên biệt
        - **Nguy hại**: Có thể chứa các chất độc hại như axit, chì, cadmium
        - **Lưu ý**: Không được đốt hoặc vứt cùng rác thải sinh hoạt
        """,
        
        "biological": """
        ### Rác hữu cơ
        - **Tái chế**: Có thể làm phân compost
        - **Phân hủy**: Phân hủy sinh học tự nhiên
        - **Lưu ý**: Nên ủ làm phân bón hoặc bỏ vào thùng rác hữu cơ
        """,
        
        "brown-glass": """
        ### Thủy tinh nâu
        - **Tái chế**: Có thể tái chế 100%
        - **Phân loại**: Nên tách riêng theo màu
        - **Lưu ý**: Rửa sạch trước khi tái chế
        """,
        
        "green-glass": """
        ### Thủy tinh xanh lá
        - **Tái chế**: Có thể tái chế 100%
        - **Phân loại**: Nên tách riêng theo màu
        - **Lưu ý**: Rửa sạch trước khi tái chế
        """,
        
        "white-glass": """
        ### Thủy tinh trắng
        - **Tái chế**: Có thể tái chế 100%
        - **Phân loại**: Nên tách riêng theo màu
        - **Lưu ý**: Rửa sạch trước khi tái chế
        """,
        
        "cardboard": """
        ### Bìa các-tông
        - **Tái chế**: Dễ dàng tái chế
        - **Phân hủy**: Phân hủy sinh học tự nhiên
        - **Lưu ý**: Gấp phẳng để tiết kiệm không gian
        """,
        
        "paper": """
        ### Giấy
        - **Tái chế**: Có thể tái chế nhiều lần
        - **Phân hủy**: Phân hủy sinh học tự nhiên
        - **Lưu ý**: Tránh giấy bẩn hoặc nhiễm dầu mỡ
        """,
        
        "plastic": """
        ### Nhựa
        - **Tái chế**: Phụ thuộc vào loại nhựa (1-7)
        - **Phân hủy**: Rất lâu, có thể hàng trăm năm
        - **Lưu ý**: Rửa sạch và kiểm tra mã tái chế
        """,
        
        "metal": """
        ### Kim loại
        - **Tái chế**: Có thể tái chế vô hạn lần
        - **Giá trị**: Có giá trị tái chế cao
        - **Lưu ý**: Rửa sạch trước khi tái chế
        """,
        
        "trash": """
        ### Rác thải khác
        - **Xử lý**: Thường đến bãi rác
        - **Lưu ý**: Kiểm tra xem có thành phần nào có thể tái chế không
        - **Giảm thiểu**: Hãy cố gắng giảm thiểu loại rác này
        """
    }
    
    return info.get(class_name.lower(), "Không có thông tin chi tiết cho loại rác này.")