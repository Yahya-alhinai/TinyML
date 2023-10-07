import argparse
import torch
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
import torch.nn as nn
import torch.optim as optim
from help_code_demo import ToTensor, IEGM_DataSET
from models.model_5_test import IEGMNet
import random
import numpy as np

def main():
    # Hyperparameters
    BATCH_SIZE = args.batchsz
    BATCH_SIZE_TEST = args.batchsz
    LR = args.lr
    EPOCH = args.epoch
    SIZE = args.size
    path_data = args.path_data
    path_indices = args.path_indices

    # torch.manual_seed(args.seed) 
    # random.seed(args.seed)
    # np.random.seed(args.seed)
    # torch.backends.cudnn.deterministic = True #reproducibility
    # torch.backends.cudnn.benchmark = False

    # Instantiating NN
    net = IEGMNet()
    net.train()
    net = net.float().to(device)

    # Start dataset loading
    trainset = IEGM_DataSET(root_dir=path_data,
                            indice_dir=path_indices,
                            mode='train',
                            size=SIZE,
                            transform=transforms.Compose([ToTensor()]))

    trainloader = DataLoader(trainset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)

    testset = IEGM_DataSET(root_dir=path_data,
                           indice_dir=path_indices,
                           mode='test',
                           size=SIZE,
                           transform=transforms.Compose([ToTensor()]))

    testloader = DataLoader(testset, batch_size=BATCH_SIZE_TEST, shuffle=True, num_workers=0)

    print("Training Dataset loading finish.")

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(net.parameters(), lr=LR, betas=(0.9, 0.999), eps=1e-8)
    epoch_num = EPOCH
    warmup_epoch = args.warmup_epoch
    steps_per_epoch = (len(trainloader))
    warmup_step = warmup_epoch * steps_per_epoch
    total_step = EPOCH * steps_per_epoch
    step = 0
    scheduler = optim.lr_scheduler.CosineAnnealingLR(
            optimizer, total_step - warmup_step, eta_min=1e-6)
    # scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=args.patience)

    Train_loss = []
    Train_acc = []
    Test_loss = []
    Test_acc = []

    print("Start training")
    for epoch in range(epoch_num):  # loop over the dataset multiple times (specify the #epoch)

        running_loss = 0.0
        correct = 0.0
        accuracy = 0.0
        i = 0
        for j, data in enumerate(trainloader, 0):
            if step < warmup_step:
                curr_lr = LR #* step / warmup_step
                optimizer.param_groups[0]['lr'] = curr_lr
            else:
                scheduler.step()

            inputs, labels = data['IEGM_seg'], data['label']
            inputs = inputs.float().to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = net(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            _, predicted = torch.max(outputs.data, 1)
            correct += (predicted == labels).sum()
            accuracy += correct / BATCH_SIZE
            correct = 0.0

            running_loss += loss.item()
            i += 1
            step += 1

        print('[Epoch, Batches] is [%d, %5d] \nTrain Acc: %.5f Train loss: %.5f' %
              (epoch + 1, i, accuracy / i, running_loss / i))

        Train_loss.append(running_loss / i)
        Train_acc.append((accuracy / i).item())

        running_loss = 0.0
        accuracy = 0.0

        correct = 0.0
        total = 0.0
        i = 0.0
        running_loss_test = 0.0

        for data_test in testloader:
            net.eval()
            IEGM_test, labels_test = data_test['IEGM_seg'], data_test['label']
            IEGM_test = IEGM_test.float().to(device)
            labels_test = labels_test.to(device)
            outputs_test = net(IEGM_test)
            _, predicted_test = torch.max(outputs_test.data, 1)
            total += labels_test.size(0)
            correct += (predicted_test == labels_test).sum()

            loss_test = criterion(outputs_test, labels_test)
            running_loss_test += loss_test.item()
            i += 1

        print('Test Acc: %.5f Test Loss: %.5f' % (correct / total, running_loss_test / i))

        Test_loss.append(running_loss_test / i)
        Test_acc.append((correct / total).item())

    torch.save(net, './saved_models/IEGM_net.pkl')
    torch.save(net.state_dict(), './saved_models/IEGM_net_state_dict.pkl')

    file = open('./saved_models/loss_acc.txt', 'w')
    file.write("Train_loss\n")
    file.write(str(Train_loss))
    file.write('\n\n')
    file.write("Train_acc\n")
    file.write(str(Train_acc))
    file.write('\n\n')
    file.write("Test_loss\n")
    file.write(str(Test_loss))
    file.write('\n\n')
    file.write("Test_acc\n")
    file.write(str(Test_acc))
    file.write('\n\n')

    print('Finish training')


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--epoch', type=int, help='epoch number', default=35)
    argparser.add_argument('--warmup_epoch', type=int, help='warmup epoch number', default=1)
    argparser.add_argument('--lr', type=float, help='learning rate', default=0.005)
    argparser.add_argument('--patience', type=float, help='patience for lr', default=10)
    argparser.add_argument('--batchsz', type=int, help='total batchsz for traindb', default=32)
    argparser.add_argument('--cuda', type=int, default=0)
    argparser.add_argument('--seed', type=int, default=1000)
    argparser.add_argument('--size', type=int, default=1250)
    argparser.add_argument('--path_data', type=str, default='./data/tinyml_contest_data_training/')
    argparser.add_argument('--path_indices', type=str, default='./data_indices')

    args = argparser.parse_args()


    device = torch.device("cpu")

    print("device is --------------", device)

    main()
