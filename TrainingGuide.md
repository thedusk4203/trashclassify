# Hướng Dẫn Huấn Luyện Mô Hình Phân Loại Rác

Tài liệu này trình bày cách huấn luyện mô hình phân loại rác thải trong ứng dụng ECO CLASSIFY. Mô hình sử dụng phương pháp transfer learning với MobileNetV2 để nhận dạng các loại rác.

## Yêu Cầu Sẵn Sàng

- Python 3.6 trở lên
- TensorFlow 2.x và các thư viện phụ trợ
- Các gói cần thiết (cài đặt bằng `pip install -r requirements.txt`)
- Dataset gồm ảnh rác đã phân loại theo thư mục

## Cấu Trúc Dataset

Dataset cần sắp xếp như sau:

```
rubbish-data/
├── train/
│   ├── battery/
│   ├── biological/
│   ├── brown-glass/
│   ├── cardboard/
│   ├── green-glass/
│   ├── metal/
│   ├── paper/
│   ├── plastic/
│   ├── trash/
│   └── white-glass/
├── val/
│   ├── battery/
│   ├── biological/
│   └── ... (tương tự train)
└── test/
    ├── battery/
    ├── biological/
    └── ... (tương tự train)
```

Mỗi thư mục chứa ảnh tương ứng với loại rác.

## Quy Trình Huấn Luyện

1. **Tải và Chuẩn bị dữ liệu**
   - Đọc ảnh từ thư mục dataset
   - Áp dụng data augmentation cho tập huấn luyện (xoay, dịch, cắt, phóng to, lật)
   - Chuẩn hóa pixel về khoảng [-1, 1]

2. **Xây dựng kiến trúc mô hình**
   - Sử dụng MobileNetV2 pre-trained trên ImageNet làm base model
   - Thêm các lớp phân loại tùy chỉnh phía trên (GlobalAveragePooling2D, Dense, Dropout)
   - Đóng băng (freeze) các lớp của base model ở giai đoạn đầu

3. **Huấn luyện hai giai đoạn**
   - **Giai đoạn 1**: Huấn luyện chỉ các lớp thêm mới (top layers)
   - **Giai đoạn 2**: Fine-tuning, mở khóa (unfreeze) 20 lớp cuối của base model và huấn luyện với learning rate thấp hơn

4. **Đánh giá mô hình**
   - Đánh giá trên tập test
   - Lưu số liệu đánh giá vào file JSON
   - Vẽ biểu đồ kết quả accuracy và loss

## Cấu Hình Huấn Luyện

Các tham số có thể điều chỉnh trong `train_model.py`:

- `IMG_SIZE`: kích thước đầu vào ảnh (mặc định 224 × 224)
- `BATCH_SIZE`: số ảnh mỗi batch (mặc định 32)
- `EPOCHS`: số epoch cho giai đoạn fine-tuning (mặc định 20)
- Learning rate cho từng giai đoạn

## Thực Thi Huấn Luyện

1. Chuẩn bị dataset theo cấu trúc đã nêu
2. Đặt thư mục `rubbish-data` trong thư mục dự án
3. Chạy script huấn luyện:

```bash
python train_model.py
```

4. Theo dõi tiến trình huấn luyện trên console
5. Sau khi hoàn thành, mô hình và file liên quan sẽ được lưu trong thư mục `model/`

## Giám sát và Điều Chỉnh

- Theo dõi giá trị loss và accuracy cho tập train và validation
- Sử dụng EarlyStopping để dừng khi không cải thiện

## Các File Kết Quả

- `model/trash_classification_model.h5`: file mô hình đã huấn luyện
- `model/class_names.txt`: danh sách tên lớp
- `model/training_history.png`: biểu đồ quá trình huấn luyện
- `prediction_stats.json`: thống kê độ chính xác và loss

## Tối Ưu Hiệu Suất

- Mở rộng dataset với ảnh đa dạng hơn
- Điều chỉnh tham số data augmentation
- Thay đổi learning rate hoặc số lớp unfreeze
- Thử nghiệm các kiến trúc base model khác (ví dụ: EfficientNet)

## Khắc Phục Sự Cố

- **Lỗi OOM**: giảm `BATCH_SIZE`
- **Overfitting**: tăng dữ liệu, thêm Dropout hoặc EarlyStopping
- **Underfitting**: tăng số epoch hoặc unfreeze thêm lớp
- **Mất cân bằng lớp**: sử dụng class weights hoặc cân bằng dataset

## Sử Dụng Mô Hình Đã Huấn Luyện

Đặt các file mô hình vào thư mục `model/`:

- `trash_classification_model.h5`
- `class_names.txt`

Ứng dụng Flask sẽ tự động tải và sử dụng khi khởi động.