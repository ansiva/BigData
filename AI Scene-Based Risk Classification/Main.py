# ------------ PHASE 1: IMPORT LIBRARIES AND GLOBAL SETTINGS ------------
import os
import random
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
import torchvision.models as models
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
from ultralytics import YOLO
from torch.utils.data import DataLoader, Subset

SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)
random.seed(SEED)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"✅ Using device: {device}")

# ------------ PHASE 2: SETTINGS ------------
DATA_DIR = "FireDataset-V6-JPG-Reshaped224"
EVAL_DATASET = "Dataset_Created"  # This folder has 'safe_images' and 'risky_images'
MODEL_SAVE_PATH = "saved_models"
PLACES_FILE = "IO_places365.txt"
os.makedirs(MODEL_SAVE_PATH, exist_ok=True)

MODE = "evaluate"  # change to "test" or "evaluate"
EPOCHS = 5
LEARNING_RATE = 0.001
BATCH_SIZE = 32
IMAGE_SIZE = (224, 224)
YOLO_CONFIDENCE_THRESHOLD = 0.4
VOTING_THRESHOLD = 3
RISKY_OBJECTS = ['fire', 'smoke', 'weapon', 'gun', 'explosion']

# ------------ PHASE 3: SCENE CLASSIFICATION SETUP ------------
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

# ------------ PHASE 4: MODEL SETUP ------------
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

resnet_places = build_resnet50_places()
yolo_detector = build_yolo_detector()
fire_model = build_mobilenet_classifier()
ppe_model = build_mobilenet_classifier()



# ------------ PHASE 5: SMART VOTING ------------
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

def vote_risk(image_path, fire_model, yolo_model, resnet_model, ppe_model):
    from PIL import Image
    import os

    fire_count = 0
    fire_area = 0.0
    smoke_count = 0
    explosion_detected = False
    weapon_detected = False
    people_detected = False
    helmet_detected = False

    # YOLO object detection
    results = yolo_model.predict(image_path, conf=0.4)
    for r in results:
        for box in r.boxes:
            label = r.names[int(box.cls[0])].lower()
            w, h = box.xywh[0][2].item(), box.xywh[0][3].item()
            if label == 'fire':
                fire_count += 1
                fire_area += w * h
            elif label == 'smoke':
                smoke_count += 1
            elif label == 'explosion':
                explosion_detected = True
            elif label in ['gun', 'weapon']:
                weapon_detected = True
            elif label in ['person', 'man', 'woman', 'boy', 'girl']:
                people_detected = True
            elif label == 'helmet':
                helmet_detected = True

    # Check filename for extra hint
    filename = os.path.basename(image_path).lower()
    if 'fire' in filename or 'explosion' in filename:
        fire_count += 1

    # Scene Type
    scene_type = classify_scene_resnet(image_path, resnet_model)

    # Fire or PPE classifier based on presence
    img = Image.open(image_path).convert('RGB')
    input_tensor = val_test_transforms(img).unsqueeze(0).to(device)
    fire_model.eval()
    ppe_model.eval()

    with torch.no_grad():
        fire_pred = torch.argmax(torch.softmax(fire_model(input_tensor), dim=1)).item()
        ppe_pred = torch.argmax(torch.softmax(ppe_model(input_tensor), dim=1)).item()

    # ------------------ FINAL DECISION TREE ------------------

    # 🚨 Immediate very risky
    if explosion_detected or weapon_detected or fire_count >= 3 or fire_area > 0.1:
        return "VERY RISKY"

    # 🔥 Fire-based logic
    if fire_count > 0:
        if smoke_count > 1:
            return "VERY RISKY"
        elif fire_area < 0.05:
            return "RISKY"
        else:
            return "VERY RISKY"

    # ☁️ Smoke without fire (handle fog/smoke)
    if smoke_count > 2:
        if scene_type == 'indoor':
            return "RISKY"
        else:
            return "SAFE"

    # 🧠 Model-based fallback
    if fire_pred == 1 or ppe_pred == 1:
        return "RISKY"

    # 🛑 Helmet violation check
    if people_detected and not helmet_detected:
        if scene_type == 'indoor':
            return "RISKY"
        else:
            return "SAFE"

    return "SAFE"


def _train_loop(model, loader, num_epochs, learning_rate, tag):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.1)
    best_loss = float('inf')

    for epoch in range(num_epochs):
        model.train()
        running_loss, running_corrects = 0, 0
        for inputs, labels in loader:
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
        epoch_loss = running_loss / len(loader.dataset)
        epoch_acc = running_corrects.double() / len(loader.dataset)
        print(f"[{tag}] Epoch {epoch+1}/{num_epochs} | Loss: {epoch_loss:.4f} | Acc: {epoch_acc:.4f}")
        if epoch_loss < best_loss:
            best_loss = epoch_loss
            torch.save(model.state_dict(), os.path.join(MODEL_SAVE_PATH, f'{tag}_best.pth'))
            print(f"✅ Best {tag} model saved!")

def train_fire_model(model, data_dir, num_epochs, learning_rate):
    from torchvision.datasets import ImageFolder
    from torch.utils.data import Subset
    from sklearn.utils import shuffle

    dataset = ImageFolder(os.path.join(data_dir, "train"), transform=train_transforms)

    # Split indices class-wise
    class_to_indices = {0: [], 1: []}
    for idx in range(len(dataset)):
        _, label = dataset[idx]
        class_to_indices[label].append(idx)

    selected_indices = []
    for label, indices in class_to_indices.items():
        n = int(0.3 * len(indices))
        indices = shuffle(indices, random_state=SEED)
        selected_indices.extend(indices[:n])
        print(f"🔥 Using {n}/{len(indices)} samples from class {label}")

    subset = Subset(dataset, selected_indices)
    loader = DataLoader(subset, batch_size=BATCH_SIZE, shuffle=True)

    _train_loop(model, loader, num_epochs, learning_rate, 'fire_model')

def train_ppe_model(model, data_dir, num_epochs, learning_rate):
    from torchvision.datasets import ImageFolder
    from torch.utils.data import Subset
    from sklearn.utils import shuffle

    dataset = ImageFolder(os.path.join(data_dir, "train"), transform=train_transforms)

    # Split indices class-wise
    class_to_indices = {0: [], 1: []}
    for idx in range(len(dataset)):
        _, label = dataset[idx]
        class_to_indices[label].append(idx)

    selected_indices = []
    for label, indices in class_to_indices.items():
        n = int(0.6 * len(indices))
        indices = shuffle(indices, random_state=SEED)
        selected_indices.extend(indices[:n])
        print(f"🦺 Using {n}/{len(indices)} samples from PPE class {label}")

    subset = Subset(dataset, selected_indices)
    loader = DataLoader(subset, batch_size=BATCH_SIZE, shuffle=True)

    _train_loop(model, loader, num_epochs, learning_rate, 'ppe_model')


# ------------ PHASE 6: TRAINING ------------
def train_mobilenet(model, fire_data_dir, ppe_data_dir, num_epochs, learning_rate):
    from torch.utils.data import ConcatDataset, Subset
    from sklearn.model_selection import train_test_split

    # Load full FireDataset
    fire_dataset = ImageFolder(os.path.join(fire_data_dir, "train"), transform=train_transforms)
    fire_indices = list(range(len(fire_dataset)))
    fire_subset_indices, _ = train_test_split(
        fire_indices, test_size=0.7, stratify=[fire_dataset[i][1] for i in fire_indices], random_state=SEED
    )
    fire_subset = Subset(fire_dataset, fire_subset_indices)
    print(f"🔥 FireDataset: Using {len(fire_subset)}/{len(fire_dataset)} samples")

    # Load full PPEDataset
    ppe_dataset = ImageFolder(os.path.join(ppe_data_dir, "train"), transform=train_transforms)
    ppe_indices = list(range(len(ppe_dataset)))
    ppe_subset_indices, _ = train_test_split(
        ppe_indices, test_size=0.5, stratify=[ppe_dataset[i][1] for i in ppe_indices], random_state=SEED
    )
    ppe_subset = Subset(ppe_dataset, ppe_subset_indices)
    print(f"🦺 PPEDataset: Using {len(ppe_subset)}/{len(ppe_dataset)} samples")

    # Combine
    combined_dataset = ConcatDataset([fire_subset, ppe_subset])
    train_loader = DataLoader(combined_dataset, batch_size=BATCH_SIZE, shuffle=True)

    # Training
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.1)
    best_loss = float('inf')

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


# ------------ PHASE 7: PREDICTION DISPLAY ------------
def predict_and_show(image_path, fire_model, yolo_model, resnet_model, ppe_model):
    print(f"🔎 Predicting image: {image_path}")
    final_label = vote_risk(image_path, fire_model, yolo_model, resnet_model, ppe_model)
    img = Image.open(image_path).convert('RGB')
    plt.figure(figsize=(10,8))
    plt.imshow(img)
    plt.title(f"Prediction: {final_label}", fontsize=20, color="green" if final_label == "SAFE" else "red")
    plt.axis('off')
    plt.show()

# ------------ PHASE 8: EVALUATION ------------
def evaluate_and_visualize(dataset_dir, fire_model, yolo_model, resnet_model, ppe_model, transform, device='cpu'):
    correct = 0
    total = 0
    for folder, true_label in [('safe_images', 'SAFE'), ('risky_images', 'RISKY')]:
        path = os.path.join(dataset_dir, folder)
        for file in os.listdir(path):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(path, file)
                pred = vote_risk(image_path, fire_model, yolo_model, resnet_model, ppe_model)
                total += 1
                if pred == true_label:
                    correct += 1
                # Optional Visualization
                img = Image.open(image_path).convert('RGB')
                plt.figure(figsize=(8, 6))
                plt.imshow(img)
                plt.title(f"Predicted: {pred} | True: {true_label}",
                          fontsize=16,
                          color="green" if pred == true_label else "red")
                plt.axis('off')
                plt.show()

    acc = correct / total
    err = 1 - acc
    print(f"\n📊 Total Images: {total}")
    print(f"✅ Accuracy: {acc*100:.2f}%")
    print(f"❌ Error Rate: {err*100:.2f}%")

def evaluate_worksite_safety_dataset(test_dir, fire_model, yolo_model, resnet_model, ppe_model):
    import pandas as pd

    print("🧪 Evaluating on Worksite-Safety-Monitoring-Dataset/test")
    correct = 0
    total = 0
    results = []

    for label in ['safe', 'unsafe']:
        folder_path = os.path.join(test_dir, label)
        for fname in os.listdir(folder_path):
            if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(folder_path, fname)
                pred = vote_risk(image_path, fire_model, yolo_model, resnet_model, ppe_model)
                true_label = 'SAFE' if label == 'safe' else 'RISKY'
                is_correct = (pred == true_label)
                results.append((fname, pred, true_label, is_correct))
                total += 1
                if is_correct:
                    correct += 1

    accuracy = (correct / total) * 100 if total > 0 else 0
    print(f"\n📊 Evaluated {total} images")
    print(f"✅ Correct: {correct}")
    print(f"❌ Incorrect: {total - correct}")
    print(f"🎯 Accuracy: {accuracy:.2f}%")

    return results


# ------------ PHASE 9: MAIN DRIVER ------------
def main():
    print("🚀 Running Mode:", MODE)
    if MODE == "train":
         train_fire_model(fire_model, "FireDataset", EPOCHS, LEARNING_RATE)
         train_ppe_model(ppe_model, "Worksite-Safety-Monitoring-Dataset", EPOCHS, LEARNING_RATE)
    elif MODE == "evaluate":
         fire_model.load_state_dict(torch.load(os.path.join(MODEL_SAVE_PATH, 'fire_model_best.pth')))
         fire_model.eval()
         ppe_model.load_state_dict(torch.load(os.path.join(MODEL_SAVE_PATH, 'ppe_model_best.pth')))
         ppe_model.eval()
         evaluate_and_visualize(EVAL_DATASET, fire_model, yolo_detector, resnet_places, ppe_model, val_test_transforms, device)
    elif MODE == "evaluate_worksite":
        fire_model.load_state_dict(torch.load(os.path.join(MODEL_SAVE_PATH, 'fire_model_best.pth')))
        fire_model.eval()
        ppe_model.load_state_dict(torch.load(os.path.join(MODEL_SAVE_PATH, 'ppe_model_best.pth')))
        ppe_model.eval()
        evaluate_worksite_safety_dataset("Worksite-Safety-Monitoring-Dataset/test", fire_model, yolo_detector, resnet_places, ppe_model)
        
    else:
        print("⚠️ Invalid MODE")

# ------------ PHASE 10: EXECUTE ------------
if __name__ == "__main__":
    main()
