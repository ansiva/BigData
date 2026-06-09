# ------------ PHASE 1: IMPORT LIBRARIES AND GLOBAL SETTINGS ------------
import os
import random
import numpy as np
import time
from PIL import Image, ImageFont
import matplotlib.pyplot as plt
import seaborn as sns
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
import torchvision.models as models
from torch.utils.data import DataLoader, Subset
from torchvision.datasets import ImageFolder

from ultralytics import YOLO
from sklearn.metrics import confusion_matrix, classification_report

SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)
random.seed(SEED)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"✅ Using device: {device}")

# Paths
DATA_DIR = "Worksite-Safety-Monitoring-Dataset"
MODEL_SAVE_PATH = "saved_models"
OUTPUT_FOLDER = "predicted_outputs"
PLACES_FILE = "IO_places365.txt"
os.makedirs(MODEL_SAVE_PATH, exist_ok=True)

# ------------ PHASE 2: MODE AND CONTROL SETTINGS ------------
MODE = "test"  # <<< Change to 'train' if you want training
EPOCHS = 10
LEARNING_RATE = 0.001
BATCH_SIZE = 32
IMAGE_SIZE = (224, 224)
RISKY_OBJECTS = ['fire', 'smoke', 'weapon', 'gun', 'explosion']
YOLO_CONFIDENCE_THRESHOLD = 0.4
VOTING_THRESHOLD = 2

# ------------ PHASE 3: DATA PREPARATION ------------
def load_indoor_scenes(file_path=PLACES_FILE):
    indoor_scenes = set()
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            for line in f.readlines():
                scene, label = line.strip().split()
                if label == '1':
                    indoor_scenes.add(scene.replace('/', '_'))
        print(f"✅ Loaded {len(indoor_scenes)} indoor scenes.")
    else:
        print("⚠️ IO_places365.txt missing.")
    return indoor_scenes

indoor_scenes = load_indoor_scenes()

train_transforms = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.RandomResizedCrop(224),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

val_test_transforms = transforms.Compose([
    transforms.Resize(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

if MODE == "test":
    full_train_dataset = ImageFolder(os.path.join(DATA_DIR, "train"), transform=train_transforms)
    train_size = int(0.7 * len(full_train_dataset))
    train_dataset = Subset(full_train_dataset, list(range(train_size)))
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    class_names = full_train_dataset.classes
    print(f"✅ Loaded {len(train_dataset)} training samples.")

# ------------ PHASE 4: BUILD MODELS ------------
def build_resnet50_places():
    model = models.resnet50(weights='IMAGENET1K_V2')
    model.fc = nn.Linear(model.fc.in_features, 365)
    return model.to(device)

def build_yolo_detector():
    return YOLO('yolov8n.pt')

def build_mobilenet_classifier():
    model = models.mobilenet_v3_small(weights='IMAGENET1K_V1')
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, 2)
    return model.to(device)

print("🔵 Initializing models...")
resnet_places = build_resnet50_places()
yolo_detector = build_yolo_detector()
mobilenet_safety = build_mobilenet_classifier()
print("✅ Models ready!")

# ------------ PHASE 5: SMART VOTING SYSTEM ------------
def clean_scene_name(scene):
    return scene.replace(' ', '_').lower()

def classify_scene_resnet(img_path, resnet_model):
    resnet_model.eval()
    img = Image.open(img_path).convert('RGB')
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    input_img = transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        output = resnet_model(input_img)
        probs = torch.softmax(output, dim=1)
        top1_idx = torch.argmax(probs).item()
    try:
        with open('categories_places365.txt') as f:
            categories = [line.strip().split(' ')[0][3:] for line in f]
        scene_label = categories[top1_idx]
    except:
        scene_label = "unknown"
    cleaned_scene = clean_scene_name(scene_label)
    return 'indoor' if cleaned_scene in indoor_scenes else 'outdoor'

def vote_risk(image_path, yolo_model, mobilenet_model, resnet_model):
    votes = 0
    yolo_detections = []
    risky_found = False
    people_detected = False
    helmet_detected = False
    animal_detected = False

    results = yolo_model.predict(image_path, conf=YOLO_CONFIDENCE_THRESHOLD)
    for r in results:
        for box in r.boxes:
            label = r.names[int(box.cls[0])]
            yolo_detections.append(label.lower())
            if label.lower() in RISKY_OBJECTS:
                risky_found = True
            if label.lower() in ['person', 'man', 'woman', 'boy', 'girl']:
                people_detected = True
            if label.lower() == 'helmet':
                helmet_detected = True
            if label.lower() in ['dog', 'cat', 'cow', 'horse']:
                animal_detected = True

    # Fallback for fire/smoke in filename
    filename = os.path.basename(image_path).lower()
    if "fire" in filename or "smoke" in filename:
        risky_found = True

    img = Image.open(image_path).convert('RGB')
    input_img = val_test_transforms(img).unsqueeze(0).to(device)
    mobilenet_model.eval()
    with torch.no_grad():
        output = mobilenet_model(input_img)
        probs = torch.softmax(output, dim=1)
        mobile_pred = torch.argmax(probs).item()

    scene_type = classify_scene_resnet(image_path, resnet_model)

    # Voting Adjustments
    if risky_found:
        votes += 3  # 🚨 Strong fire/smoke detected → Stronger risky signal
    if mobile_pred == 1:
        votes += 2  # MobileNet says risky
    if scene_type == 'indoor' and people_detected and not helmet_detected:
        votes += 2  # Indoors, people seen, but no helmets → risky
    if scene_type == 'outdoor' and people_detected and not helmet_detected:
        votes += 1
    if animal_detected:
        votes -= 1

    final_label = "RISKY" if votes >= 2 else "SAFE"
    print(f"🗳️ Voting Result: {votes} votes --> {final_label}")
    return final_label

# ------------ PHASE 6: TRAIN FUNCTION (if needed) ------------
def train_mobilenet(model, train_loader, num_epochs, learning_rate):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.1)
    best_loss = np.inf

    for epoch in range(num_epochs):
        model.train()
        running_loss, running_corrects = 0, 0
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            preds = torch.argmax(outputs, 1)
            running_loss += loss.item() * inputs.size(0)
            running_corrects += torch.sum(preds == labels)
        scheduler.step()
        epoch_loss = running_loss / len(train_loader.dataset)
        epoch_acc = running_corrects.double() / len(train_loader.dataset)
        print(f"Epoch {epoch+1}/{num_epochs} | Loss: {epoch_loss:.4f} | Acc: {epoch_acc:.4f}")
        if epoch_loss < best_loss:
            best_loss = epoch_loss
            torch.save(model.state_dict(), os.path.join(MODEL_SAVE_PATH, 'mobilenet_best.pth'))
            print("✅ Best MobileNet model saved!")

# ------------ PHASE 7: PREDICTION FUNCTION ------------

def predict_and_show(image_path, mobilenet_model, yolo_model, resnet_model):
    print(f"🔎 Predicting image: {image_path}")
    final_label = vote_risk(image_path, yolo_model, mobilenet_model, resnet_model)
    img = Image.open(image_path).convert('RGB')
    plt.figure(figsize=(10,8))
    plt.imshow(img)
    plt.title(f"Prediction: {final_label}", fontsize=20, color="green" if final_label == "SAFE" else "red")
    plt.axis('off')
    plt.show()

# ------------ PHASE 8: MAIN DRIVER ------------

def main():
    print("🚀 Starting Safety Prediction Pipeline...")
    if MODE == "train":
        history = train_mobilenet(mobilenet_safety, train_loader, EPOCHS, LEARNING_RATE)
    elif MODE == "test":
        print("✅ Loading MobileNet pre-trained weights...")
        mobilenet_safety.load_state_dict(torch.load(os.path.join(MODEL_SAVE_PATH, 'mobilenet_best.pth')))
        mobilenet_safety.eval()
        test_images = [
            "earthquake1.png"
            
        ]
        for img_path in test_images:
            predict_and_show(img_path, mobilenet_safety, yolo_detector, resnet_places)
    else:
        print("⚠️ Invalid MODE selected!")


# ------------ PHASE 13: TEST ON FULL TEST SET ------------

def test_on_full_testset(mobilenet_model, yolo_model, resnet_model, test_folder_path):
    print("\n🚀 Starting Full Test Set Evaluation...")

    test_images = []
    test_labels = []

    # Load SAFE images
    safe_dir = os.path.join(test_folder_path, 'safe')
    for img_file in os.listdir(safe_dir):
        if img_file.endswith(('.jpg', '.jpeg', '.png')):
            test_images.append(os.path.join(safe_dir, img_file))
            test_labels.append('SAFE')

    # Load RISKY images
    unsafe_dir = os.path.join(test_folder_path, 'unsafe')
    for img_file in os.listdir(unsafe_dir):
        if img_file.endswith(('.jpg', '.jpeg', '.png')):
            test_images.append(os.path.join(unsafe_dir, img_file))
            test_labels.append('RISKY')

    # Limit number of test images
    MAX_TEST_IMAGES = 10
    test_images = test_images
    test_labels = test_labels

    correct = 0
    total = 0

    for img_path, true_label in zip(test_images, test_labels):
        pred_label = vote_risk(
            image_path=img_path,
            yolo_model=yolo_model,
            mobilenet_model=mobilenet_model,
            resnet_model=resnet_model
        )

        total += 1
        if pred_label == true_label:
            correct += 1

       
        img = Image.open(img_path).convert('RGB')
        plt.figure(figsize=(8, 8))
        plt.imshow(img)
        plt.title(f"Prediction: {pred_label}",
                  fontsize=18, color="green" if pred_label == "SAFE" else "red")
        plt.axis('off')
        plt.show()

    # Accuracy
    accuracy = correct / total
    error_rate = 1 - accuracy
    print(f"\n✅ Test Set Accuracy: {accuracy*100:.2f}%")
    print(f"❌ Test Set Error Rate: {error_rate*100:.2f}%")

def evaluate_test_set(mobilenet_model, yolo_model, resnet_model, test_folder_path):
    print("\n🚀 Starting True Evaluation on Full Test Set...")

    test_images = []
    true_labels = []

    # Gather test images and true labels
    for label_folder, label_name in [('safe', 'SAFE'), ('unsafe', 'RISKY')]:
        folder_path = os.path.join(test_folder_path, label_folder)
        for img_file in os.listdir(folder_path):
            if img_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                test_images.append(os.path.join(folder_path, img_file))
                true_labels.append(label_name)

    # Run predictions
    predicted_labels = []

    for img_path in test_images:
        pred_label = vote_risk(
            image_path=img_path,
            yolo_model=yolo_model,
            mobilenet_model=mobilenet_model,
            resnet_model=resnet_model
        )
        predicted_labels.append(pred_label)

    # Calculate results
    correct = sum([p == t for p, t in zip(predicted_labels, true_labels)])
    total = len(true_labels)
    accuracy = correct / total
    error_rate = 1 - accuracy

    # Summaryx
    print(f"\n📈 Evaluation Results:")
    print(f"Total Images: {total}")
    print(f"Correct Predictions: {correct}")
    print(f"Wrong Predictions: {total - correct}")
    print(f"✅ Accuracy: {accuracy*100:.2f}%")
    print(f"❌ Error Rate: {error_rate*100:.2f}%")

    return accuracy, error_rate

if __name__ == "__main__":
    main()
  
    test_on_full_testset(mobilenet_safety, yolo_detector, resnet_places, os.path.join(DATA_DIR, 'test'))
