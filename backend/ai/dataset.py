from pathlib import Path
from PIL import Image

from torch.utils.data import Dataset
from torchvision import transforms


class PlantVillageDataset(Dataset):
    def __init__(self, image_paths, labels, train=True):

        self.image_paths = image_paths
        self.labels = labels

        if train:
            self.transform = transforms.Compose([
                transforms.Resize((224,224)),
                transforms.RandomHorizontalFlip(),
                transforms.RandomRotation(20),
                transforms.ColorJitter(
                    brightness=0.2,
                    contrast=0.2,
                    saturation=0.2
                ),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485,0.456,0.406],
                    std=[0.229,0.224,0.225]
                )
            ])
        else:

            self.transform = transforms.Compose([
                transforms.Resize((224,224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485,0.456,0.406],
                    std=[0.229,0.224,0.225]
                )
            ])

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self,index):

        image = Image.open(self.image_paths[index]).convert("RGB")

        image = self.transform(image)

        label = self.labels[index]

        return image,label