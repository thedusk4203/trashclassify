import os
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
import json

# Configuration
IMG_SIZE = 224  # MobileNetV2 input size requirement
BATCH_SIZE = 32
EPOCHS = 20
BASE_DIR = 'rubbish-data'
MODEL_DIR = 'model'
MODEL_PATH = os.path.join(MODEL_DIR, 'trash_classification_model.h5')

# Ensure model directory exists
os.makedirs(MODEL_DIR, exist_ok=True)

# Get class names from directory structure
train_dir = os.path.join(BASE_DIR, 'train')
classes = sorted([d for d in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, d))])
num_classes = len(classes)

print(f"Trash classification classes: {classes}")
print(f"Total number of classes: {num_classes}")

# Data generators with augmentation for training set
train_datagen = ImageDataGenerator(
    preprocessing_function=lambda x: x / 127.5 - 1,  # Normalize to [-1, 1]
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

# Only normalization for validation and test sets
val_datagen = ImageDataGenerator(preprocessing_function=lambda x: x / 127.5 - 1)
test_datagen = ImageDataGenerator(preprocessing_function=lambda x: x / 127.5 - 1)

# Create data generators
train_generator = train_datagen.flow_from_directory(
    os.path.join(BASE_DIR, 'train'),
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=True
)

validation_generator = val_datagen.flow_from_directory(
    os.path.join(BASE_DIR, 'val'),
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=False
)

test_generator = test_datagen.flow_from_directory(
    os.path.join(BASE_DIR, 'test'),
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    shuffle=False
)

# Save class mapping for later use
class_indices = train_generator.class_indices
class_names = {v: k for k, v in class_indices.items()}

# Print class indices for reference
print("Class indices mapping:")
for class_name, idx in class_indices.items():
    print(f"{idx}: {class_name}")

# Save class names to file
with open(os.path.join(MODEL_DIR, 'class_names.txt'), 'w') as f:
    for i in range(len(class_names)):
        f.write(f"{class_names[i]}\n")

# Build model with transfer learning using MobileNetV2
# Load pre-trained model without top layers
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(IMG_SIZE, IMG_SIZE, 3))

# Freeze base model layers
for layer in base_model.layers:
    layer.trainable = False

# Add custom classification head
x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dense(512, activation='relu')(x)
x = Dropout(0.5)(x)  # Prevent overfitting
predictions = Dense(num_classes, activation='softmax')(x)

# Create final model
model = Model(inputs=base_model.input, outputs=predictions)

# Compile model
model.compile(
    optimizer=Adam(learning_rate=0.001),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# Print model summary
model.summary()

# Callbacks for training
checkpoint = ModelCheckpoint(
    MODEL_PATH,
    monitor='val_accuracy',
    save_best_only=True,
    verbose=1
)

early_stopping = EarlyStopping(
    monitor='val_loss',
    patience=5,
    restore_best_weights=True,
    verbose=1
)

reduce_lr = ReduceLROnPlateau(
    monitor='val_loss',
    factor=0.2,
    patience=3,
    min_lr=1e-6,
    verbose=1
)

callbacks = [checkpoint, early_stopping, reduce_lr]

# Phase 1: Train only the top layers
print("Starting training phase 1 (top layers only)...")
history = model.fit(
    train_generator,
    steps_per_epoch=train_generator.samples // BATCH_SIZE,
    validation_data=validation_generator,
    validation_steps=validation_generator.samples // BATCH_SIZE,
    epochs=10,
    callbacks=callbacks
)

# Phase 2: Fine-tuning - unfreeze some layers of the base model
print("Fine-tuning the last layers of base model...")
for layer in base_model.layers[-20:]:
    layer.trainable = True

# Recompile model with lower learning rate for fine-tuning
model.compile(
    optimizer=Adam(learning_rate=0.0001),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# Continue training with fine-tuning
print("Starting training phase 2 (fine-tuning)...")
history_fine = model.fit(
    train_generator,
    steps_per_epoch=train_generator.samples // BATCH_SIZE,
    validation_data=validation_generator,
    validation_steps=validation_generator.samples // BATCH_SIZE,
    epochs=EPOCHS,
    callbacks=callbacks
)

# Evaluate model on test set
print("Evaluating model on test set...")
test_loss, test_acc = model.evaluate(test_generator, steps=test_generator.samples // BATCH_SIZE)
print(f"Test accuracy: {test_acc:.4f}")
print(f"Test loss: {test_loss:.4f}")

# Save test evaluation metrics
evaluation_stats = {
    "test_accuracy": float(test_acc),
    "test_loss": float(test_loss),
    "classes": classes,
    "num_classes": num_classes,
    "image_size": IMG_SIZE,
    "final_epoch_val_accuracy": float(history_fine.history['val_accuracy'][-1]),
    "final_epoch_val_loss": float(history_fine.history['val_loss'][-1])
}

with open('prediction_stats.json', 'w') as f:
    json.dump(evaluation_stats, f, indent=4)

# Plot training results
plt.figure(figsize=(12, 4))

# Plot training & validation accuracy
plt.subplot(1, 2, 1)
plt.plot(history_fine.history['accuracy'])
plt.plot(history_fine.history['val_accuracy'])
plt.title('Model Accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper left')

# Plot training & validation loss
plt.subplot(1, 2, 2)
plt.plot(history_fine.history['loss'])
plt.plot(history_fine.history['val_loss'])
plt.title('Model Loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper left')

plt.tight_layout()
plt.savefig(os.path.join(MODEL_DIR, 'training_history.png'))
plt.show()

print(f"Model saved at: {MODEL_PATH}")
print("Training completed!")