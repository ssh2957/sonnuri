### Copyright (C) 2017 NVIDIA Corporation. All rights reserved. 
### Licensed under the CC BY-NC-SA 4.0 license (https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode).
import os.path
import random
import torchvision.transforms as transforms
import torch
from data.base_dataset import BaseDataset, get_params, get_transform, normalize
from data.image_folder import make_dataset
from PIL import Image
import numpy as np

class AlignedDataset(BaseDataset):
    def initialize(self, opt):
        self.opt = opt
        self.root = opt.dataroot    

        ### label maps    
        self.dir_label = os.path.join(opt.dataroot, opt.phase + '_label/')
        print(f"Label directory path: {self.dir_label}")  # 디버깅 출력
        self.label_paths = sorted(make_dataset(self.dir_label))
        print(f"label_paths: {self.label_paths}")  # 디버깅 출력

        ### real images
        if opt.isTrain:
            self.dir_image = os.path.join(opt.dataroot, opt.phase + '_img')  
            self.image_paths = sorted(make_dataset(self.dir_image))

        ### load face bounding box coordinates size 128x128
        if opt.face_discrim or opt.face_generator:
            self.dir_facetext = os.path.join(opt.dataroot, opt.phase + '_facetexts128')
            print('----------- loading face bounding boxes from %s ----------' % self.dir_facetext)
            self.facetext_paths = sorted(make_dataset(self.dir_facetext))


        self.dataset_size = len(self.label_paths) 
      
    def __getitem__(self, index):
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        target_size = (self.opt.fineSize, self.opt.fineSize)  # 목표 크기 설정
                
        ### label maps
        paths = self.label_paths
        label_path = paths[index]              
        label = Image.open(label_path).convert('RGB')
        label = label.resize(target_size, Image.BICUBIC)  # 크기 조정        
        params = get_params(self.opt, label.size)
        transform_label = get_transform(self.opt, params, method=Image.NEAREST, normalize=False)
        label_tensor = transform_label(label).float().to(device)
        original_label_path = label_path

        image_tensor = next_label = next_image = face_tensor = 0
        
        # zeroshere 텐서 생성
        zeroshere = torch.zeros_like(label_tensor).to(device)

        ### real images 
        if self.opt.isTrain:
            image_path = self.image_paths[index]   
            image = Image.open(image_path).convert('RGB')
            image = image.resize(target_size, Image.BICUBIC)  # 크기 조정    
            transform_image = get_transform(self.opt, params)     
            image_tensor = transform_image(image).float().to(device)

        is_next = index < len(self) - 1
        if self.opt.gestures:
            is_next = is_next and (index % 64 != 63)

        """ Load the next label, image pair """
        if is_next:
            paths = self.label_paths
            label_path = paths[index+1]              
            label = Image.open(label_path).convert('RGB')
            label = label.resize(target_size, Image.BICUBIC)  # 크기 조정        
            params = get_params(self.opt, label.size)          
            transform_label = get_transform(self.opt, params, method=Image.NEAREST, normalize=False)
            next_label = transform_label(label).float().to(device)
            
            if self.opt.isTrain:
                image_path = self.image_paths[index+1]   
                image = Image.open(image_path).convert('RGB')
                image = image.resize(target_size, Image.BICUBIC)  # 크기 조정
                transform_image = get_transform(self.opt, params)      
                next_image = transform_image(image).float().to(device)

        """ If using the face generator and/or face discriminator """
        if self.opt.face_discrim or self.opt.face_generator:
            facetxt_path = self.facetext_paths[index]
            facetxt = open(facetxt_path, "r")
            face_tensor = torch.IntTensor(list([int(coord_str) for coord_str in facetxt.read().split()])).to(device)

        input_dict = {'label': label_tensor, 
                    'image': image_tensor, 
                    'path': original_label_path, 
                    'face_coords': face_tensor,
                    'next_label': next_label, 
                    'next_image': next_image,
                    'zeroshere': zeroshere}  # zeroshere 추가

        return input_dict

    def __len__(self):
        return len(self.label_paths)

    def name(self):
        return 'AlignedDataset'