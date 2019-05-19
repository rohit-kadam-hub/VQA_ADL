from all_imports import *
from func_defs import *
import argparse
from iwimodel import IWIModel
from prep_data import get_data

class PrependModel(tf.keras.Model):
	def __init__(self, ans_len, que_len):
		super(PrependModel, self).__init__()
		self.flatten = tf.keras.layers.Flatten()
		self.condense = tf.keras.layers.Dense(64, activation="relu")
		self.embedding = tf.keras.layers.Embedding(input_dim=que_len + 1,output_dim=64) 
		self.gru = tf.keras.layers.GRU(256, return_sequences=False, return_state=False)
		self.logits = tf.keras.layers.Dense(ans_len, activation="softmax")

	def call(self, x, sents):
		flat_out = self.flatten(x)
		cond_out = self.condense(flat_out)
		cond_out = tf.expand_dims(cond_out, axis=1)
		sents = self.embedding(sents)
		input_s = tf.concat([cond_out, sents], axis=1)
		output = self.gru(input_s)
		final = self.logits(output)
		return final

	def init_state(self, batch_s):
		return tf.zeros((batch_s, 256))


class PrependImageAsWordModel(tf.keras.Model):
	def __init__(self, ans_len, que_len):
		self.embedding_size = 128
		self.rnn_size = 512
		super(PrependImageAsWordModel, self).__init__()
		self.flatten = tf.keras.layers.Flatten()
		self.condense = tf.keras.layers.Dense(self.embedding_size, activation='relu')
		
		# add embedding layer for questions
		self.embedding = tf.keras.layers.Embedding(input_dim=que_len + 1, output_dim=self.embedding_size)
		
		# create the input
		self.gru = tf.keras.layers.GRU(self.rnn_size,
									  return_sequences=False,
									  return_state=False)
		self.logits = tf.keras.layers.Dense(ans_len, activation='softmax')
		
	def call(self, x, sents):
		flattended_output = self.flatten(x)
		condensed_out = self.condense(flattended_output)
		#     print(condensed_out.shape)
		condensed_out = tf.expand_dims(condensed_out, axis=1)
		#     print(condensed_out.shape)
		sents = self.embedding(sents)
		#     print(sents.shape)
		input_s = tf.concat([condensed_out, sents], axis=1)
		#     print(input_s.shape)
		output = self.gru(input_s)
		final_output = self.logits(output)
		return final_output
	  

class AppendImageAsWordModel(tf.keras.Model):
	def __init__(self, ans_len, que_len):
		super(AppendImageAsWordModel, self).__init__()
		self.embedding_size = 128
		self.rnn_size = 512
		self.flatten = tf.keras.layers.Flatten()
		self.condense = tf.keras.layers.Dense(self.embedding_size, activation='relu')
    
		# add embedding layer for questions
		self.embedding = tf.keras.layers.Embedding(input_dim=que_len + 1, output_dim=self.embedding_size)
    
		# create the input
		self.gru = tf.keras.layers.GRU(self.rnn_size,
									  return_sequences=False,
									  return_state=False)
		self.logits = tf.keras.layers.Dense(ans_len, activation='softmax')
    
	def call(self, x, sents):
		flattended_output = self.flatten(x)
		condensed_out = self.condense(flattended_output)
		#     print(condensed_out.shape)
		condensed_out = tf.expand_dims(condensed_out, axis=1)
		#     print(condensed_out.shape)
		sents = self.embedding(sents)
		#     print(sents.shape)
		input_s = tf.concat([sents, condensed_out], axis=1)
		#     print(input_s.shape)
		output = self.gru(input_s)
		final_output = self.logits(output)
		#     print(final_output.shape)
		return final_output
		
		
class SeparateImageAsWordModel(tf.keras.Model):
	def __init__(self, ans_len, que_len):
		super(SeparateImageAsWordModel, self).__init__()
		self.embedding_size = 128
		self.rnn_size = 512
		self.flatten = tf.keras.layers.Flatten()
		self.condense = tf.keras.layers.Dense(self.embedding_size, activation='relu')
		
		# add embedding layer for questions
		self.embedding = tf.keras.layers.Embedding(input_dim=que_len + 1, output_dim=self.embedding_size)
		
		# create the input
		self.gru = tf.keras.layers.GRU(self.rnn_size,
									  return_sequences=False,
									  return_state=False)
		self.logits = tf.keras.layers.Dense(ans_len, activation='softmax')
    
	def call(self, x, sents):
		flattended_output = self.flatten(x)
		condensed_out = self.condense(flattended_output)
		#     print(condensed_out.shape)
		condensed_out = tf.expand_dims(condensed_out, axis=1)
		#     print(condensed_out.shape)
		sents = self.embedding(sents)
		sent_lstm_output = self.gru(sents)  # run LSTM on question sents
		sent_lstm_output = tf.expand_dims(sent_lstm_output, axis=1)
		#     print(sent_lstm_output.shape)
		output = tf.concat([sent_lstm_output, condensed_out], axis=2) # word and image embeddings side by side
		#     print(output.shape)
		final_output = self.logits(output)
		return final_output
		
		
class AlternatingCoattentionModel(tf.keras.Model):
	def __init__(self, ans_len, que_len,max_q):
		super(AlternatingCoattentionModel, self).__init__(name='AlternatingCoattentionModel')
		self.max_q = max_q
		self.ip_dense = Dense(256, activation='relu', input_shape=(512,)) 
		num_words = que_len+2
		self.word_level_feats = Embedding(input_dim = que_len+2,output_dim = 256)
		self.lstm_layer = LSTM(256,return_sequences=True,input_shape=(None,max_q,256)) 
		self.dropout_layer = Dropout(0.5)
		self.tan_layer = Activation('tanh')
		self.phrase_level_unigram = Conv1D(256,kernel_size=256,strides=256) 
		self.phrase_level_bigram = Conv1D(256,kernel_size=2*256,strides=256,padding='same') 
		self.phrase_level_trigram = Conv1D(256,kernel_size=3*256,strides=256,padding='same') 
		self.dense_image = Dense(256, activation='relu', input_shape=(256,))
		self.dense_text = Dense(256, activation='relu', input_shape=(256,))
		self.image_attention = Dense(1, activation='softmax', input_shape=(256,))
		self.text_attention = Dense(1, activation='softmax', input_shape=(256,)) 
		self.dense_word_level = Dense(256, activation='relu', input_shape=(256,)) 
		self.dense_phrase_level = Dense(256, activation='relu', input_shape=(2*256,)) 
		self.dense_sent_level = Dense(256, activation='relu', input_shape=(2*256,)) 
		self.dense_final = Dense(ans_len, activation='relu', input_shape=(256,))
		
    
	def affinity(self,image_feat,text_feat,g,prev_att):
		V_ = self.dense_image(image_feat)
		Q_ = self.dense_text(text_feat)
		
		if g==0:
			temp1 = self.tan_layer(Q_)
			H_text = self.dropout_layer(temp1) 
			return H_text
	
		elif g==1:
			g = self.dense_text(prev_att)   
			g = tf.expand_dims(g,1)
			temp = V_ + g
			temp = self.tan_layer(temp)
			H_img = self.dropout_layer(temp)
			return H_img
	  
		elif g==2:
			g = self.dense_image(prev_att)
			g = tf.expand_dims(g,1)
			temp = Q_ + g
			temp = self.tan_layer(temp)
			H_text = self.dropout_layer(temp)
			return H_text
	
  
	def attention_ques(self,text_feat,H_text):
		temp = self.text_attention(H_text)
		return tf.reduce_sum(temp * text_feat,1) 
  
  
	def attention_img(self,image_feat,H_img):
		temp = self.image_attention(H_img)
		return tf.reduce_sum(temp * image_feat,1)
	
	def call(self,image_feat,question_encoding):
		# Processing the image
		image_feat = self.ip_dense(image_feat) 

		# Text fetaures 

		# Text: Word level
		word_feat = self.word_level_feats(question_encoding) 

		# Text: Phrase level
		word_feat_ = tf.reshape(word_feat,[word_feat.shape[0], 1, -1])
		word_feat_= tf.transpose(word_feat_, perm=[0,2,1]) 
		uni_feat = self.phrase_level_unigram(word_feat_)
		uni_feat = tf.expand_dims(uni_feat,-1) 
		bi_feat = self.phrase_level_bigram(word_feat_) 
		bi_feat = tf.expand_dims(bi_feat,-1)
		tri_feat = self.phrase_level_trigram(word_feat_)
		tri_feat = tf.expand_dims(tri_feat,-1)
		all_feat = tf.concat([uni_feat, bi_feat, tri_feat],-1)
		phrase_feat = tf.reduce_max(all_feat,-1) 

		# Text: Sentence level
		sent_feat = self.lstm_layer(phrase_feat) 

		#Apply attention to features at all three levels

		# Applying attention on word level features
		word_H_text = self.affinity(image_feat,word_feat,0,0)
		word_text_attention = self.attention_ques(word_feat,word_H_text)
		word_H_img = self.affinity(image_feat,word_feat,1,word_text_attention)
		word_img_attention = self.attention_img(image_feat,word_H_img)
		word_H_text = self.affinity(image_feat,word_feat,2,word_img_attention)
		word_text_attention = self.attention_ques(word_feat,word_H_text)

		word_level_attention = word_img_attention + word_text_attention
		word_pred = self.dropout_layer(self.tan_layer(self.dense_word_level(word_level_attention)))

		# Applying attention on sentence level features
		sent_H_text = self.affinity(image_feat,sent_feat,0,0)
		sent_text_attention = self.attention_ques(sent_feat,sent_H_text)
		sent_H_img = self.affinity(image_feat,sent_feat,1,sent_text_attention)
		sent_img_attention = self.attention_img(image_feat,sent_H_img)
		sent_H_text = self.affinity(image_feat,sent_feat,2,sent_img_attention)
		sent_text_attention = self.attention_ques(sent_feat,sent_H_text)

		sentence_level_attention = tf.concat([sent_img_attention + sent_text_attention, word_pred],-1) 
		sent_pred = self.dropout_layer(self.tan_layer(self.dense_sent_level(sentence_level_attention)))

		return self.dense_final(sent_pred)