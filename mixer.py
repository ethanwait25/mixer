import librosa
import pydub
import numpy as np
import soundfile as sf

def getKey(index):
    chromaToKey = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    return chromaToKey[index]

class Track:
    def __init__(self, path):
        self.y, self.sr = librosa.load(path)

        tempo, self.beatFrames = librosa.beat.beat_track(y=self.y, sr=self.sr)
        self.tempo = tempo.item() if isinstance(tempo, np.ndarray) else tempo
        self.beatTimes = librosa.frames_to_time(self.beatFrames, sr=self.sr)

        chromagram = librosa.feature.chroma_stft(y=self.y, sr=self.sr)
        meanChroma = np.mean(chromagram, axis=1)
        keyIndex = np.argmax(meanChroma)
        self.key = getKey(keyIndex)  

    def changeTempo(self, newTempo):
        adjustFactor = newTempo / self.tempo
        self.y = librosa.effects.time_stretch(self.y, rate=adjustFactor)
        self.tempo = newTempo

    def changeKey(self, dSemitones):
        newThing = None
        self.key = getKey(newThing)

    def writeOut(self, savePath):
        sf.write(savePath, self.y, self.sr)


class Mixer:
    def __init__(self, f1, f2):
        self.track1 = Track(f1)
        self.track2 = Track(f2)

    def getTracks(self):
        return self.track1, self.track2
    
    def mix(self, savePath, mode="faster"):
        self.__matchTempo(mode)
        self.__matchKey()
        self.__writeOut(savePath)

    def __matchTempo(self, mode):
        if mode == "faster":
            masterTrack = self.track1 if self.track1.tempo > self.track2.tempo else self.track2
            slaveTrack = self.track1 if masterTrack == self.track2 else self.track2
            slaveTrack.changeTempo(masterTrack.tempo)
        elif mode == "slower":
            slaveTrack = self.track1 if self.track1.tempo > self.track2.tempo else self.track2
            masterTrack = self.track1 if slaveTrack == self.track2 else self.track2
            slaveTrack.changeTempo(masterTrack.tempo)
        elif mode == "mean":
            meanTempo = (self.track1.tempo + self.track2.tempo) / 2
            self.track1.changeTempo(meanTempo)
            self.track2.changeTempo(meanTempo)

    def __matchKey(self):

    def __writeOut(self, savePath):
        

mixer = Mixer("flow.mp3", "sax.mp3")