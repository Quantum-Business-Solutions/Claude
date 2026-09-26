# Generative ambient bed: slow pad chords + soft pulse, 44.1k stereo, ~12 min. Original, no samples.
import numpy as np, wave
SR=44100; BPM=76; beat=60/BPM; bar=4*beat
prog=[[48,55,59,64],[45,52,57,60,64],[41,48,55,57,64],[43,50,55,59,62]]  # Cmaj7, Am7, Fmaj7(9), G6
def f(n): return 440*2**((n-69)/12)
dur=12*60+10; N=int(SR*dur); L=np.zeros(N); R=np.zeros(N)
t_bar=int(SR*bar*2)  # each chord 2 bars
rng=np.random.default_rng(7)
def env(n,att,rel):
    e=np.ones(n); a=int(att*SR); r=int(rel*SR)
    e[:a]=np.linspace(0,1,a)**2; e[-r:]*=np.linspace(1,0,r)**2; return e
pos=0; ci=0
while pos<N:
    ch=prog[ci%4]; n=min(t_bar+int(SR*3), N-pos); tt=np.arange(n)/SR
    e=env(n,2.5,3.0)
    for k,note in enumerate(ch):
        fr=f(note); det=1+0.0025*(k%2*2-1)
        s=(np.sin(2*np.pi*fr*tt)+0.35*np.sin(2*np.pi*fr*2*tt+0.3)+0.12*np.sin(2*np.pi*fr*3*tt))*0.5
        s2=(np.sin(2*np.pi*fr*det*tt+1.1)+0.3*np.sin(2*np.pi*fr*det*2*tt))*0.5
        pan=0.3+0.4*(k/len(ch))
        L[pos:pos+n]+=e*(s*(1-pan)+s2*0.5)/len(ch); R[pos:pos+n]+=e*(s*pan+s2*0.5)/len(ch)
    # soft bass
    b=f(ch[0]-12); bs=np.sin(2*np.pi*b*tt)*env(n,1.5,3.0)*0.35
    L[pos:pos+n]+=bs; R[pos:pos+n]+=bs
    pos+=t_bar; ci+=1
# gentle eighth-note pluck arpeggio (very quiet)
step=int(SR*beat/2); pos=0; i=0
while pos+step<N:
    ch=prog[(pos//t_bar)%4]; note=ch[[0,2,1,3,2,1,3,2][i%8]%len(ch)]+12
    n=int(SR*0.9); n=min(n,N-pos); tt=np.arange(n)/SR
    p=np.sin(2*np.pi*f(note)*tt)*np.exp(-tt*5)*0.06*(0.8+0.4*rng.random())
    L[pos:pos+n]+=p*0.7; R[pos:pos+n]+=p
    pos+=step; i+=1
# simple smoothing lowpass + normalise
k=np.ones(8)/8; L=np.convolve(L,k,'same'); R=np.convolve(R,k,'same')
# fade in/out
fi=int(SR*4); fo=int(SR*6); ramp=np.ones(N); ramp[:fi]=np.linspace(0,1,fi); ramp[-fo:]=np.linspace(1,0,fo)
L*=ramp; R*=ramp
m=max(np.abs(L).max(),np.abs(R).max()); L=L/m*0.6; R=R/m*0.6
st=(np.stack([L,R],1)*32767).astype(np.int16)
w=wave.open('music_bed.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()
print('ok',dur)
