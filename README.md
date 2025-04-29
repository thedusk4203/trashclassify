# Phân Loại Rác Thải ♻️

Ứng dụng phân loại rác thải sử dụng Deep Learning để nhận dạng và phân loại rác thải thành 10 loại khác nhau.

## Giới thiệu

Ứng dụng này giúp người dùng nhận biết loại rác thải qua hình ảnh, hỗ trợ việc phân loại rác thải đúng cách. Dự án sử dụng:
- TensorFlow/Keras cho mô hình Deep Learning
- Streamlit cho giao diện người dùng
- OpenCV cho xử lý hình ảnh

## Cách sử dụng

1. Truy cập ứng dụng
2. Tải lên hình ảnh rác thải của bạn
3. Nhấn nút "Phân loại" 
4. Xem kết quả phân loại và thông tin về cách xử lý rác thải đó

## Các loại rác thải được phân loại

- Pin/Ắc quy (Battery)
- Rác hữu cơ (Biological)
- Thủy tinh (Nâu, Xanh lá, Trắng)
- Bìa các-tông (Cardboard)
- Giấy (Paper)
- Nhựa (Plastic)
- Kim loại (Metal)
- Rác thải khác (Trash)

## Hướng dẫn phát triển

### Cài đặt môi trường

```bash
pip install -r requirements.txt
```

### Chạy ứng dụng

```bash
streamlit run app_streamlit.py
```

## Nguồn dữ liệu

Mô hình được huấn luyện trên bộ dữ liệu rác thải với hơn 2500 hình ảnh thuộc 10 loại rác thải khác nhau.
