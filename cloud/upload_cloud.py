from . import cloud_speech
from wav_read import WavInfo
from word_error_rate.wer_improve import wer


def upload_and_record(db, sid, path):

    unit, reading_len, content = db.get_reading_content(sid)

    destination_blob_name = 'unit ' + str(unit) + '/' + sid + '.wav'
    cloud_speech.upload_blob("speech_to_text_class", path, destination_blob_name)
    gcs_url = "gs://speech_to_text_class/" + destination_blob_name
    number_of_channels, frame_rate = WavInfo.get_wav_frame(path)
    transcript, transcript_len, confidence = cloud_speech.transcribe_gcs(gcs_url, number_of_channels, frame_rate)

    reading_time = WavInfo.get_wav_time(path)
    reading_speed = int(transcript_len / (reading_time / 60.0))
    word_error_rate = (1 - wer(content, transcript)) * 100
    word_error_rate = float('%.4f' % word_error_rate)

    db.record_reading(sid, unit, transcript, reading_speed, word_error_rate, confidence)
