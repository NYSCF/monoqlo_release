from keras import models
from keras_retinanet import models as krmodels

def load_models(global_model_path='Models/multi_class_v1-1_epoch12.h5',
                local_model_path='Models/interm_v1-1.h5',
                sc_model_path='Models/sc_augmented_v0.0.h5', # Single cell model
                class_model_path = 'Models/2019-07-22onTG3_chkpt_model.22-acc0.94_V1.hdf5'):

    global_model = krmodels.load_model(global_model_path, backbone_name='resnet50')
    local_model = krmodels.load_model(local_model_path, backbone_name='resnet50')
    single_cell_model = krmodels.load_model(sc_model_path, backbone_name='resnet50')
    class_model = models.load_model(class_model_path)

    pmodels = [global_model, local_model, single_cell_model, class_model]

    return pmodels