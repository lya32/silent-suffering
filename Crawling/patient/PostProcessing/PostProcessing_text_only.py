from pyspark import SparkContext, SparkConf
import nltk
nltk.download()
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import re, unicodedata
import sys
import json
import os

def transform(line):
    contraction_mapping = {"ive":"i have","dont":"do not","doesnt":"does not","cant":"can not","isnt":"is not","ain't": "is not", "aren't": "are not","can't": "cannot", "'cause": "because", "could've": "could have", "couldn't": "could not", "didnt": "did not","didn't": "did not",  "doesn't": "does not", "don't": "do not", "hadn't": "had not", "hasn't": "has not", "havent":"have not","haven't": "have not", "he'd": "he would","he'll": "he will", "he's": "he is", "how'd": "how did", "how'd'y": "how do you", "how'll": "how will", "how's": "how is",  "I'd": "I would", "I'd've": "I would have", "I'll": "I will", "I'll've": "I will have","I'm": "I am", "I've": "I have", "i'd": "i would", "i'd've": "i would have", "i'll": "i will",  "i'll've": "i will have","i'm": "i am", "i've": "i have", "isn't": "is not", "it'd": "it would", "it'd've": "it would have", "it'll": "it will", "it'll've": "it will have","it's": "it is", "let's": "let us", "ma'am": "madam", "mayn't": "may not", "might've": "might have","mightn't": "might not","mightn't've": "might not have", "must've": "must have", "mustn't": "must not", "mustn't've": "must not have", "needn't": "need not", "needn't've": "need not have","o'clock": "of the clock", "oughtn't": "ought not", "oughtn't've": "ought not have", "shan't": "shall not", "sha'n't": "shall not", "shan't've": "shall not have", "she'd": "she would", "she'd've": "she would have", "she'll": "she will", "she'll've": "she will have", "she's": "she is", "should've": "should have", "shouldn't": "should not", "shouldn't've": "should not have", "so've": "so have","so's": "so as", "this's": "this is","that'd": "that would", "that'd've": "that would have", "that's": "that is", "there'd": "there would", "there'd've": "there would have", "there's": "there is", "here's": "here is","they'd": "they would", "they'd've": "they would have", "they'll": "they will", "they'll've": "they will have", "they're": "they are", "they've": "they have", "to've": "to have", "wasn't": "was not", "we'd": "we would", "we'd've": "we would have", "we'll": "we will", "we'll've": "we will have", "we're": "we are", "we've": "we have", "weren't": "were not", "what'll": "what will", "what'll've": "what will have", "what're": "what are",  "what's": "what is", "what've": "what have", "when's": "when is", "when've": "when have", "where'd": "where did", "where's": "where is", "where've": "where have", "who'll": "who will", "who'll've": "who will have", "who's": "who is", "who've": "who have", "why's": "why is", "why've": "why have", "will've": "will have", "won't": "will not", "won't've": "will not have", "would've": "would have", "wouldn't": "would not", "wouldn't've": "would not have", "y'all": "you all", "y'all'd": "you all would","y'all'd've": "you all would have","y'all're": "you all are","y'all've": "you all have","you'd": "you would", "you'd've": "you would have", "you'll": "you will", "you'll've": "you will have", "you're": "you are", "you've": "you have" }
    domain_maping = {" dr. ": "doctor", " docs ":" doctor ", " doc s ": " doctor ", " dr ": " doctor ", " drs ": " doctor ", " doc ":" doctor ", " med s ": " medication ", " meds ": " medication ", " med ": " medication ", " appt ": "appointment", " doesn t ": " does not ", " isn t ": " is not ", " wasn t ": " was not ", " don t ": " do not ", " haven t ": " have not "}
    for key, value in domain_maping.items():
        line = re.sub(key, value, line)
    line = re.sub(r'\?+', "? ", line)
    line = re.sub(r'\!+', "! ", line)
    line = re.sub(r'\.+\n*', " . ", line)
    line = re.sub(r',[\w+\s]', ", ", line)
    """Convert all characters to lowercase"""
    line = line.lower().replace('"',' " ').replace(':',' : ').replace('\n', ' ').replace('/', ' ').replace('_', ' ')
    if "." not in line[-3:] and "?" not in line[-3:] and "!" not in line[-3:]:
        line = line + ' .'
    word_list = []
    for word in line.split():
        new_word = word
        """Remove punctuation except for "?" and "!" from list of tokenized words"""
        if contraction_mapping.__contains__(new_word):
            new_word = contraction_mapping[new_word]
        word_list.append(new_word)
    return ' '.join(word_list)

def normalize(word):
    """Remove non-ASCII characters from list of tokenized words"""
    new_word = unicodedata.normalize('NFKD', word).encode('ascii', 'ignore').decode('utf-8', 'ignore')
    new_word = re.sub(r'[^\w\s\.\!\?\:\,\-\(\)}]', '', new_word)
    lemmatizer = WordNetLemmatizer()
    # new_word = lemmatizer.lemmatize(new_word, pos='v')
    new_word = lemmatizer.lemmatize(new_word, pos='n')
    return new_word

def sent_preprocessing(sent):
    return " ".join([normalize(word) for word in word_tokenize(transform(sent)) if normalize(word) != ""]).strip()

def merge(post_reply):
    content_id = post_reply[0]
    group = post_reply[1][0][2]
    result = []
    post_dict = post_reply[1][0][0]
    post_dict["content_id"] = content_id + "-0"
    post_dict["post_type"] = "discussion"
    post_dict["group"] = group
    result.append(post_dict)

    count = 0
    for reply in post_reply[1]:
        for each in reply[1].values():
            count += 1
            each["content_id"] = content_id + "-" + str(count)
            each["post_type"] = "reply"
            each["group"] = group
            result.append(each)

    # Code below is to merge replies to dicscussion
    # for reply in post_reply[1]:
    #     for each in reply[1].values():
    #         post_dict['text'] += '\n' + each['text']
    # result.append(post_dict)
    
    return result


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(sys.stderr,"<input_dict_path>")
        exit(-1)

    # for local debug
    # input_path = 'PatientDiscussion.jl'
    # output_path = 'PatientDiscussion_merged.jl'
    os.makedirs("data_processed_entry_text_only_nonlemmatize")
    directory_name = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    for each in directory_name:
        os.makedirs("data_processed_entry_text_only_nonlemmatize/" + each)
    inputpath = sys.argv[1] + '/'
    for filename in os.listdir(inputpath):
        if filename[-2:] == 'jl':
            conf = SparkConf() \
                    .setAppName("Data_Merge_Text_Only") \
                    .set("spark.driver.memory", "32g")\
                    .set("spark.executor.memory", "16g")\
                    .set("spark.driver.host", "localhost")
            sc = SparkContext(conf=conf)

            inputData = sc.textFile(os.path.abspath(inputpath + filename))

            # merge data
            merged_data = inputData.map(lambda x: json.loads(x))\
                                .map(lambda x: (x['content_id'],(x['post'], x['reply'], x['group'])))\
                                    .groupByKey()\
                                        .flatMap(lambda x: merge((x[0], list(x[1]))))\
                                            .collect()
            
            for each in merged_data:
                outputpath = "data_processed_entry_text_only_nonlemmatize/" + filename[0] + '/' + filename[:-3] + '-' +each["content_id"] + '.txt'
                f = open(outputpath, 'w')
                f.write(sent_preprocessing(each["text"]))
                f.close()

            #Code below is to merge replies to dicscussion
            # outputpath = 'data_processed_entry/' + filename[:-3] + '_Merged_Entry.jl'
            # # write into the file
            # with open(outputpath, 'w') as f:
            #     for each in merged_data:
            #         f.write(json.dumps(each) + '\n')
            sc.stop()
