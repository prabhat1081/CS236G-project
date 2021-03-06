import os
import argparse
import numpy as np
from torch.autograd import Variable
from torchvision import datasets, transforms
import torch.utils.data
from sklearn.svm import LinearSVC
from model import *
from cifar_dataset_mnist_eval import CIFAR10_MNIST


batch_size = 64
latent_size = 256
cuda_device = "0"

parser = argparse.ArgumentParser()
parser.add_argument('--dataset', required=True, help='cifar10 | svhn')
parser.add_argument('--dataroot', default = "/atlas/u/a7b23/data", help='path to dataset')
parser.add_argument('--use_cuda', type=bool, default=True)
parser.add_argument('--model_path', required=True)

opt = parser.parse_args()

os.environ["CUDA_VISIBLE_DEVICES"] = cuda_device

def tocuda(x):
    if opt.use_cuda:
        return x.cuda()
    return x


def get_random_uniform_batch(data, targets, num_classes=10, samples_per_class=100):
    random_batch = np.zeros((num_classes*samples_per_class, data.shape[1]))
    random_targets = np.zeros(num_classes*samples_per_class)
    indices = np.random.permutation(data.shape[0])
    batch_size = 0
    label_counts = np.zeros(num_classes)
    for i in indices:
        if label_counts[targets[i]] < samples_per_class:
            label_counts[targets[i]] += 1
            random_batch[batch_size, :] = data[i, :]
            random_targets[batch_size] = targets[i]
            batch_size += 1
        if batch_size >= num_classes*samples_per_class:
            break

    return random_batch, random_targets

def get_embeddings(loader, netE, fname):
    
    all_embeddings = []
    all_targets = []

    for idx, (data, target) in enumerate(loader):
        temp, h1, h2, h3 = netE.forward(Variable(tocuda(data)))

        temp = temp.view(temp.size(0), -1)
        all_embeddings.extend(temp.cpu().data.numpy())
        all_targets.extend(target.cpu().data.numpy())
        print(idx, len(train_loader))

    all_embeddings = np.array(all_embeddings)
    all_targets = np.array(all_targets)

    print(all_embeddings.shape, all_targets.shape)

    np.save(fname, all_embeddings)
    np.save(fname.replace("feats.npy", "labels.npy"), all_targets)

if __name__ == "__main__":

    encoder_state_dict = torch.load(opt.model_path)
    netE = Encoder(latent_size, True)
    netE.load_state_dict(encoder_state_dict)
    netE = tocuda(netE)

    print("Model restored")

    if opt.dataset == 'svhn':
        train_loader = torch.utils.data.DataLoader(
            datasets.SVHN(root=opt.dataroot, split='extra', download=True,
                          transform=transforms.Compose([
                              transforms.ToTensor()
                          ])),
            batch_size=batch_size, shuffle=True)

        test_loader = torch.utils.data.DataLoader(
            datasets.SVHN(root=opt.dataroot, split='train', download=True,
                          transform=transforms.Compose([
                              transforms.ToTensor()
                          ])),
            batch_size=batch_size, shuffle=True)

    elif opt.dataset == 'cifar10':
        train_loader = torch.utils.data.DataLoader(
            datasets.CIFAR10(root=opt.dataroot, train=True, download=True,
                             transform=transforms.Compose([
                                 transforms.ToTensor()
                             ])),
            batch_size=batch_size, shuffle=True)

        test_loader = torch.utils.data.DataLoader(
            datasets.CIFAR10(root=opt.dataroot, train=False, download=True,
                             transform=transforms.Compose([
                                 transforms.ToTensor()
                             ])),
            batch_size=batch_size, shuffle=True)

    elif opt.dataset == "cifar_mnist_cifar":
        train_loader = torch.utils.data.DataLoader(
        CIFAR10_MNIST(root=opt.dataroot, aug_type = 1, train=True, download=False, dataset = "cifar",
                      transform=transforms.Compose([
                          transforms.ToTensor()
                      ])),
        batch_size=batch_size, shuffle=True)

        test_loader = torch.utils.data.DataLoader(
        CIFAR10_MNIST(root=opt.dataroot, aug_type = 1, train=False, download=False, dataset = "cifar",
                      transform=transforms.Compose([
                          transforms.ToTensor()
                      ])),
        batch_size=batch_size, shuffle=True)

    elif opt.dataset == "cifar_mnist_mnist":
        train_loader = torch.utils.data.DataLoader(
        CIFAR10_MNIST(root=opt.dataroot, aug_type = 1, train=True, download=False, dataset = "mnist",
                      transform=transforms.Compose([
                          transforms.ToTensor()
                      ])),
        batch_size=batch_size, shuffle=True)

        test_loader = torch.utils.data.DataLoader(
        CIFAR10_MNIST(root=opt.dataroot, aug_type = 1, train=False, download=False, dataset = "mnist",
                      transform=transforms.Compose([
                          transforms.ToTensor()
                      ])),
        batch_size=batch_size, shuffle=True)

    else:
        raise NotImplementedError



    get_embeddings(train_loader, netE, "feats/" + opt.dataset + "_train_feats.npy")
    get_embeddings(test_loader, netE, "feats/" + opt.dataset + "_test_feats.npy")

