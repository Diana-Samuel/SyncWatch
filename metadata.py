import ffmpeg
import hashlib
import pickle

def get_video_metadata(file_path):
    try:
        probe_output = ffmpeg.probe(file_path)
        with open(file_path, "rb") as f:
            md5 = hashlib.md5(f.read()).hexdigest()
        data = {
            "duration": probe_output["streams"][0]["duration"],
            "md5": md5
        }
        return data
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return None


metadata = get_video_metadata(input("FilePath: "))

with open("videoMetaData.vid","wb") as f:
    pickle.dump(metadata,f)