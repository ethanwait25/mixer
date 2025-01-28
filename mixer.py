import librosa
import pydub
import numpy as np
import soundfile as sf

def getKey(index):
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    return keys[index]

def getKeyIndex(key):
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    return keys.index(key)

class Track:
    def __init__(self, path):
        self.y, self.sr = librosa.load(path, sr=None)

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

    def changeKey(self, newKey):
        keyIndex = getKeyIndex(self.key)
        newKeyIndex = getKeyIndex(newKey)

        belowDist = (keyIndex - newKeyIndex) % 12
        aboveDist = (newKeyIndex - keyIndex) % 12

        dSemitones = -belowDist if belowDist < aboveDist else aboveDist
        self.y = librosa.effects.pitch_shift(self.y, sr=self.sr, n_steps=dSemitones)
        self.key = getKey(newKeyIndex)

    def changeSR(self, newSR):
        self.y = librosa.resample(self.y, orig_sr=self.sr, target_sr=newSR, res_type="kaiser_best")
        self.sr = newSR

    def writeOut(self, savePath, withAttrNames=False):
        if "." not in savePath:
            raise ValueError("savePath requires filename")
        
        if withAttrNames:
            splitPath = savePath.split(".")
            savePath = f"{splitPath[0]}-{str(int(self.tempo))}-{self.key}.{splitPath[1]}"
        sf.write("out-tracks/" + savePath, self.y, self.sr, subtype='PCM_24')


class Mixer:
    def __init__(self, f1, f2):
        self.track1 = Track(f1)
        self.track2 = Track(f2)
        self.y_combined = None
        self.sr = None

    def getTracks(self):
        return self.track1, self.track2
    
    def mix(self, savePath, tempoMode="faster", keyMode="higher"):
        self.__matchSR()
        self.__matchTempo(tempoMode)
        self.__matchKey(keyMode)
        self.__overlayTracks()
        self.__writeOut(savePath)

    def __matchSR(self):
        if self.track1.sr != self.track2.sr:
            masterTrack = self.track1 if self.track1.sr > self.track2.sr else self.track2
            servantTrack = self.track1 if masterTrack == self.track1 else self.track2
            servantTrack.changeSR(masterTrack.sr)
            self.sr = masterTrack.sr

    def __matchTempo(self, mode):
        if mode == "faster":
            masterTrack = self.track1 if self.track1.tempo > self.track2.tempo else self.track2
            servantTrack = self.track1 if masterTrack == self.track2 else self.track2
            servantTrack.changeTempo(masterTrack.tempo)
        elif mode == "slower":
            masterTrack = self.track1 if self.track1.tempo < self.track2.tempo else self.track2
            servantTrack = self.track1 if masterTrack == self.track2 else self.track2
            servantTrack.changeTempo(masterTrack.tempo)
        elif mode == "mean":
            meanTempo = (self.track1.tempo + self.track2.tempo) / 2
            self.track1.changeTempo(meanTempo)
            self.track2.changeTempo(meanTempo)
        else:
            raise ValueError("Invalid tempo mode")

    def __matchKey(self, mode):
        if mode == "higher":
            masterTrack = self.track1 if getKeyIndex(self.track1.key) > getKeyIndex(self.track2.key) else self.track2
            servantTrack = self.track1 if masterTrack == self.track2 else self.track2
            servantTrack.changeKey(masterTrack.key)
        elif mode == "lower":
            masterTrack = self.track1 if getKeyIndex(self.track1.key) < getKeyIndex(self.track2.key) else self.track2
            servantTrack = self.track1 if masterTrack == self.track2 else self.track2
            servantTrack.changeKey(masterTrack.key)
        elif mode == "mean":
            meanKeyIndex = (getKeyIndex(self.track1.key) + getKeyIndex(self.track2.key)) // 2
            meanKey = getKey(meanKeyIndex)
            self.track1.changeKey(meanKey)
            self.track2.changeKey(meanKey)
        else:
            raise ValueError("Invalid key mode")
        
    def __overlayTracks(self):
        lenDiff = len(self.track1.y) - len(self.track2.y)
        shorter = self.track1 if len(self.track1.y) < len(self.track2.y) else self.track2
        longer = self.track1 if shorter == self.track2 else self.track2

        shorterY = np.pad(shorter.y, (0, lenDiff), mode='constant')
        self.y_combined = shorterY + longer.y

    def __writeOut(self, savePath):
        if "." not in savePath:
            raise ValueError("savePath requires filename")
        sf.write("mixes/" + savePath, self.y_combined, self.sr, subtype='PCM_24')
        

mixer = Mixer("tracks/flow.mp3", "tracks/sax.mp3")
mixer.mix("flowsax.wav")

# sax = Track("tracks/sax.mp3")
# sax.changeKey("C")
# sax.changeTempo(100)
# sax.writeOut("sax.wav", True)