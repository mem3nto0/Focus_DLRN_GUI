#%%

import tensorflow as tf
from keras.models import Model
from keras.layers import Dense, Flatten, GaussianNoise
from keras.layers import Conv2D, MaxPooling2D , Add , Dropout , AveragePooling2D, Concatenate
from keras.layers import Input, Activation, Conv1D, BatchNormalization, LayerNormalization


def activated_conv2D(Input ,N_filters, kernel, strides):

    y = Conv2D(N_filters, kernel, strides= strides, use_bias=True, padding= "same")(Input)
    y = LayerNormalization()(y)
    y = Activation("relu")(y)

    return y

def res_block_inseption_A(y):

    y1 = activated_conv2D(y, 32, kernel=(1,1), strides = (1,1))

    y2 = activated_conv2D(y, 32, kernel=(1,1), strides = (1,1))
    y2 = activated_conv2D(y2, 32, kernel=(3,3), strides = (1,1))

    y3 = activated_conv2D(y, 32, kernel=(1,1), strides = (1,1))
    y3 = activated_conv2D(y3, 48, kernel=(3,3), strides = (1,1))
    y3 = activated_conv2D(y3, 64, kernel=(3,3), strides = (1,1))

    y1 = Concatenate(axis=-1)([y1,y2,y3])
    y1 = Conv2D(y.shape[-1], (1,1), padding="same")(y1)

    y = Add()([y,y1])
    y = LayerNormalization()(y)
    y = Activation("relu")(y)

    return y


def reduction_block_A(y):


    y1 = MaxPooling2D(pool_size=(3,3), strides = (2,2), padding="same")(y)

    y2 = activated_conv2D(y, 384, kernel=(3,3), strides = (2,2))

    y = activated_conv2D(y, 256, kernel=(1,1), strides = (1,1))
    y = activated_conv2D(y, 256, kernel=(3,3), strides = (1,1))
    y = activated_conv2D(y, 384, kernel=(3,3), strides = (2,2))

    y = Concatenate(axis=-1)([y1,y2,y])

    return y  

def res_block_inseption_B(y):

    y1 = activated_conv2D(y, 192, kernel=(1,1), strides = (1,1))

    y2 = activated_conv2D(y, 128, kernel=(1,1), strides = (1,1))
    y2 = activated_conv2D(y2, 160, kernel=(1,7), strides = (1,1))
    y2 = activated_conv2D(y2, 192, kernel=(7,1), strides = (1,1))

    y2 = Concatenate(axis=-1)([y1,y2])
    y2 = Conv2D(y.shape[-1], (1,1), padding="same")(y2)

    y =Add()([y,y2])
    y = LayerNormalization()(y)
    y = Activation("relu")(y)

    return y

def reduction_block_B(y):

    y1 = activated_conv2D(y, 256, kernel=(1,1), strides = (1,1))
    y1 = activated_conv2D(y1, 384, kernel=(1,1), strides = (2,2))

    y2 = activated_conv2D(y, 256, kernel=(1,1), strides = (1,1))
    y2 = activated_conv2D(y2, 384, kernel=(3,3), strides = (2,2))

    y3 = activated_conv2D(y, 256, kernel=(1,1), strides = (1,1))
    y3 = activated_conv2D(y3, 288, kernel=(3,3), strides = (1,1))
    y3 = activated_conv2D(y3, 320, kernel=(3,3), strides = (2,2))    

    y = MaxPooling2D(pool_size=(3, 3), strides = (2,2), padding="same")(y)

    y = Concatenate(axis=-1)([y,y1,y2,y3])

    return y

def res_block_inseption_C(y):

    y1 = activated_conv2D(y, 192, kernel=(1,1), strides = (1,1))

    y2 = activated_conv2D(y, 192, kernel=(1,1), strides = (1,1))
    y2 = activated_conv2D(y2, 224, kernel=(1,3), strides = (1,1))
    y2 = activated_conv2D(y2, 256, kernel=(3,1), strides = (1,1))

    y2 = Concatenate(axis=-1)([y1,y2])
    y2 = Conv2D(y.shape[-1], (1,1), padding="same")(y2)
    

    y =Add()([y,y2])
    y = LayerNormalization()(y)
    y = Activation("relu")(y)

    return y


def Res_block(y_inp, filters):

    y1 =Conv1D(filters,1,padding="same")(y_inp)

    y =Conv1D(filters,3,padding="same")(y_inp)
    y = LayerNormalization()(y) # added 2026-01 maybe to remove
    y = Activation("relu")(y)
    
    y =Conv1D(filters,3,padding="same")(y)

    y = Add()([y,y1])
    y = LayerNormalization()(y) # added 2026-01 maybe to remove
    y = Activation("relu")(y)    

    return y


"""the model is here below. function on the top of it are subfunction used for blocks"""

"""
//////////////////////////////////////
//////// DLRN MODEL         /////////
/////////////////////////////////////
"""

def get_focused_DRLN(label):

    input_layer = Input((256, 256, 1), name='input_1')
    noise = GaussianNoise(0.001)(input_layer)
    
    y = activated_conv2D(noise, 32, kernel= (3,3), strides = (2,2))
    y = activated_conv2D(y, 32, kernel=(3,3), strides = (1,1))
    y = activated_conv2D(y, 32, kernel=(3,3), strides = (1,1))
    
    y1 = y

    y1 = MaxPooling2D(pool_size=(3, 3), strides = (2,2), padding="same")(y1)
    y = activated_conv2D(y, 96, kernel= (3,3), strides = (2,2))

    y = Concatenate(axis=-1)([y1,y])

    y2 = y

    y2 = activated_conv2D(y2, 64, kernel= (1,1), strides = (1,1))
    y2 = activated_conv2D(y2, 128, kernel= (3,3), strides = (1,1))

    y = activated_conv2D(y, 64, kernel= (1,1), strides = (1,1))
    y = activated_conv2D(y, 64, kernel= (7,1), strides = (1,1))
    y = activated_conv2D(y, 64, kernel= (1,7), strides = (1,1))
    y = activated_conv2D(y, 128, kernel= (3,3), strides = (1,1))

    y = Concatenate(axis=-1)([y2,y])

    y3 = y

    y3 = MaxPooling2D((3,3), strides = (2,2), padding= "same")(y3)
    y = activated_conv2D(y, 256, kernel= (3,3), strides = (2,2))

    y = Concatenate(axis=-1)([y3,y])


    for ii in range(5):

        y = res_block_inseption_A(y)  

    y = reduction_block_A(y)

    for ii in range(10):

        y = res_block_inseption_B(y)  

    y = reduction_block_B(y)    

    for ii in range (5):

        y = res_block_inseption_C(y)

    # === MODEL prediction part ===

    y = AveragePooling2D((8,8), padding='same')(y)

    y2 = Dropout(0.2)(y)
    y2 = Flatten()(y2)       
    y2 = Dense(1024, activation= "relu")(y2)
    y2 = Dropout(0.2)(y2)
    y2 = Dense(512, activation= "relu")(y2)
   
    output_layer1 = Dense(label, activation="softmax", name='output_1')(y2)    

    # //// TAU prediction part //////
    y2_2 = Dense(512, activation="relu")(y2)
    y2_2 = Dense(512, activation="relu")(y2_2)
    y2_2 = LayerNormalization()(y2_2) # 
    y2_2 = Dropout(0.2)(y2_2)

    y1 = Dropout(0.2)(y)
    y1 = Flatten()(y1)
    y1 = Dense(1024, activation="relu")(y1) # // it is better with it //
    y1 = LayerNormalization()(y1)

    y1 = Concatenate(axis=-1)([y1, y2_2])
    y1 = Dense(896, activation="relu")(y1) 
    y1 = LayerNormalization()(y1)

    y1 = tf.keras.layers.Reshape((7,128))(y1)

    y1 = Res_block(y1, 512)
    y1 = Res_block(y1, 512)
    y1 = Res_block(y1, 512)

    y1 = Flatten()(y1)
    y1 = Dropout(0.2)(y1)

    output_layer2 = Dense(10, activation="softplus", name="output_2")(y1)

    model = Model(inputs = [input_layer], outputs = [output_layer1, output_layer2])

    return model


"""
def Res_block(y_inp, filters):

    y =Conv1D(filters // 4, 1,padding="same")(y_inp)
    y = BatchNormalization()(y) # added 2026-01 maybe to remove
    y = Activation("relu")(y)

    y =Conv1D(filters // 4, 3, padding="same")(y)
    y = BatchNormalization()(y) # added 2026-01 maybe to remove
    y = Activation("relu")(y)
    
    y =Conv1D(filters, 1 ,padding="same")(y)

    y = Add()([y, y_inp])
    y = BatchNormalization()(y) # added 2026-01 maybe to remove
    y = Activation("relu")(y)    

    return y

"""
