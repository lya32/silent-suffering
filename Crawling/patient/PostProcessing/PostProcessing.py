from pyspark import SparkContext, SparkConf
import sys
import json
import os

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
    os.makedirs("data_processed_entry")
    inputpath = sys.argv[1] + '/'
    for filename in os.listdir(inputpath):
        if filename[-2:] == 'jl':
            conf = SparkConf() \
                    .setAppName("Data_Merge") \
                    .set("spark.executor.memory", "4g")\
                    .set("spark.driver.host", "localhost")
            sc = SparkContext(conf=conf)

            inputData = sc.textFile(os.path.abspath(inputpath + filename))

            # merge data
            merged_data = inputData.map(lambda x: json.loads(x))\
                                .map(lambda x: (x['content_id'],(x['post'], x['reply'], x['group'])))\
                                    .groupByKey()\
                                        .flatMap(lambda x: merge((x[0], list(x[1]))))\
                                            .collect()
            
            os.makedirs("data_processed_entry/" + filename[:-3] + "_entry")
            for each in merged_data:
                outputpath = 'data_processed_entry/' + filename[:-3] + "_entry" + '/' + filename[:-3] + '-' +each["content_id"] + '.jl'
                f = open(outputpath, 'w')
                f.write(json.dumps(each))
                f.close()

            #Code below is to merge replies to dicscussion
            # outputpath = 'data_processed_entry/' + filename[:-3] + '_Merged_Entry.jl'
            # # write into the file
            # with open(outputpath, 'w') as f:
            #     for each in merged_data:
            #         f.write(json.dumps(each) + '\n')
            sc.stop()
