from bs4 import BeautifulSoup
import os
import re
from pymediainfo import MediaInfo


class Converter:
    def __init__(self, path):
        self.path = path

        self.stream_records = []
        self.video_streams = []

        self.__process_mainstream()

        self.size = [1920, 1088]

    def __process_mainstream(self):
        with open(os.path.join(self.path, 'mainstream.xml')) as f:
            xml = BeautifulSoup(f.read(), 'xml')
            for message in xml.find_all('Message'):
                array = message.find('Array')
                if array and array.find('Object') and array.find('Object').find('streamName'):
                    stream = [array.find('Object').find('streamName').string, int(
                        array.find('Object').find('startTime').string)]
                    try:
                        index = self.stream_records.index(stream)
                        self.stream_records[index].append(int(message['time']))
                        if self.stream_records[index][0][1] == 's':
                            self.video_streams.append(
                                self.stream_records[index])

                    except ValueError:
                        self.stream_records.append(stream)

    def __max_count_items(self, _iter):
        if _iter:
            return sorted(_iter, key=lambda x: list(_iter).count(x), reverse=True)[0]

    def set_size(self, size):
        self.size = size

    def __get_size(self):
        _all = []
        for video in self.video_streams:
            v = MediaInfo.parse(os.path.join(self.path, video[0][1:] + '.flv'))
            size = v.video_tracks[0]
            _all.append([size.width, size.height])

        return self.__max_count_items(_all)

    def __video(self):
        _input = ''
        _size = ''
        _gap = ''
        _gap_index = len(self.stream_records)
        _concat = ''
        _w_size = self.size or self.__get_size()
        for index, video in enumerate(self.video_streams):
            _input += '-i "'+os.path.join(self.path, video[0][1:])+".flv"+'" '
            #TODO: remember to change the option of force resizing
            _size += f'[{index}]scale={_w_size[0]}:{_w_size[1]}[v{index}];'
            _gap += f'[{_gap_index}]trim=duration={video[1] / 1000 if not index else (video[1] - self.video_streams[index - 1][2]) / 1000}[g{index}];'
            _concat += f'[g{index}][v{index}]'

        return _input, _size, _gap, _concat, _w_size

    def __audio(self):
        _input = ''
        _delay = ''
        _labels = ''
        index = 0
        _start_index = len(self.video_streams)

        for stream in self.stream_records:
            if stream[0][1] == 'c':
                _input += '-i "'+os.path.join(self.path, stream[0][1:])+".flv"+'" ' 
                _delay += f'[{index + _start_index}]adelay={stream[1]}|{stream[1]}[a{index}];'
                _labels += f'[a{index}]'
                index += 1

        return _input, _delay, _labels, index

    def convert(self, folder_name, file_name):
        video_input, video_size, video_gap, video_concat, _s = self.__video()
        audio_input, audio_delay, audio_labels, _len = self.__audio()

        if not os.path.isdir(folder_name):
            os.makedirs(folder_name)

        print(f'ffmpeg {video_input}{audio_input}-f lavfi -i "color=c=black:s={_s[0]}x{_s[1]}:r=1" -filter_complex "{video_size}{video_gap}{audio_delay}{audio_labels}amix=inputs={_len}:duration=longest:dropout_transition=0[outa]{";"+video_concat+"concat=n="+str(len(self.video_streams)*2)+":v=1:a=0[outv]" if self.video_streams else ""}" -map "[outa]" {"-map " + "[outv]" + " -r 24" if self.video_streams else ""} "{folder_name}/{file_name}.flv"')
        print(self.__run(f'ffmpeg {video_input}{audio_input}-f lavfi -i "color=c=black:s={_s[0]}x{_s[1]}:r=1" -filter_complex "{video_size}{video_gap}{audio_delay}{audio_labels}amix=inputs={_len}:duration=longest:dropout_transition=0[outa]{";"+video_concat+"concat=n="+str(len(self.video_streams)*2)+":v=1:a=0[outv]" if self.video_streams else ""}" -map [outa] {"-map " + "[outv]" + " -r 24" if self.video_streams else ""} "{folder_name}/{file_name}.flv"'))

    def __run(self, command):
        stream = os.popen(command)
        return stream.read()
