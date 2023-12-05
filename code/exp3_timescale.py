"""
Experiments 3: Slow inhibition by NDNF interneurons preferentially transmits certain signals.
- 
"""

import numpy as np
import matplotlib.pyplot as plt
plt.style.use('pretty')
import matplotlib as mpl
lw = mpl.rcParams['lines.linewidth']
import seaborn as sns
import model_base as mb
from experiments import get_null_ff_input_arrays, get_model_colours, plot_violin
from scipy.fft import fft, fftfreq
from detect_peaks import detect_peaks
from exp2_competition import quantify_signals

cPC, cPV, cSOM, cNDNF, cVIP, cpi = get_model_colours()

DPI = 150


def exp301_frequency_preference(noise=0.0, w_hetero=False, mean_pop=True, pre_inh=True, reduced=False, save=False):
    """
    Experiment 1: Test frequency transmission of NDNF and SOM to PC.
    """

    freqs = np.array([0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15]) #np.arange(0.5, 10, 0.5) #np.array([1, 2, 4, 8, 16])  # np.arange(1, 20)
    betas = np.array([0.5]) #np.arange(0, 0.5, 0.1)

    # define parameter dictionaries
    N_cells, w_mean, conn_prob, bg_inputs, taus = mb.get_default_params(flag_mean_pop=mean_pop)

    if reduced:  # remove 
        w_mean['EP'], w_mean['PE'], w_mean['SE'] = 0, 0, 0

    # w_mean['DS'] = 1
    # w_mean['DN'] = 1
    # TODO: remove
    # w_mean.update(dict(SV=0.4, PV=0.2, PN=0.3, VN=0.2, DE=0.2))

    # instantiate model
    model = mb.NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_w_hetero=w_hetero,
                            flag_pre_inh=pre_inh)
    
    # simulation paramters
    dur = 5000
    dt = 1
    nt = int(dur/dt)

    amplitudes_n = np.zeros(len(freqs))
    amplitudes_s = np.zeros(len(freqs))

    # fig, ax = plt.subplots(2, 1, figsize=(3, 3), dpi=150)

    amp = 1.5
    dpi = 300 if save else DPI
    fig, ax = plt.subplots(1, 1, dpi=dpi, figsize=(1.8, 1.15), gridspec_kw={'left': 0.25, 'bottom': 0.33, 'hspace':0.2, 'right':0.95})
    cols_s = sns.color_palette(f"light:{cSOM}", n_colors=len(betas)+1)[1:]
    cols_n = sns.color_palette(f"light:{cNDNF}", n_colors=len(betas)+1)[1:]

    for j, bb in enumerate(betas):
        print(f"pre inh beta = {bb:1.1f}")

        for i, ff in enumerate(freqs):

            model.b = bb

            # make input
            xff_null = np.zeros(nt)  
            xff_sine = amp*(make_sine(nt, ff)-0.5)

            # simulate with sine input to SOM
            xFF = get_null_ff_input_arrays(nt, N_cells)
            xFF['S'] = np.tile(xff_sine, [N_cells['S'], 1]).T
            xFF['N'] = np.tile(xff_null, [N_cells['N'], 1]).T
            t, rE1, rD1, rS1, rN1, rP1, rV1, p1, cGABA1, other1 = model.run(dur, xFF, dt=dt, p0=0.5, calc_bg_input=True)

            # simulate with sine input to NDNF
            xFF = get_null_ff_input_arrays(nt, N_cells)
            xFF['S'] = np.tile(xff_null, [N_cells['S'], 1]).T
            xFF['N'] = np.tile(xff_sine, [N_cells['N'], 1]).T
            t, rE2, rD2, rS2, rN2, rP2, rV2, p2, cGABA2, other2 = model.run(dur, xFF, dt=dt, p0=0.5, calc_bg_input=True)

            # quantify   
            # TODO: how to quantify? Fourier analysis? peak-to-trough?
            # freqs1, power1, perHz1 = fft_signal_contribution(np.mean(rE1, axis=1))
            # freqs2, power2, perHz2 = fft_signal_contribution(np.mean(rE2, axis=1))
            # # print(ff, freqs[ind], power[ind])

            # amplitudes_s[i] = power1[int(ff*perHz1)]
            # amplitudes_n[i] = power2[int(ff*perHz2)]

            # TODO: not sure Fourier is the right measure...

            amplitudes_s[i] = signal_amplitude(np.mean(rD1, axis=1), tstart=int(1000*dt))
            amplitudes_n[i] = signal_amplitude(np.mean(rD2, axis=1), tstart=int(1000*dt))

            # if i%5 == 0:
            #     fig1, ax1 = plt.subplots(1, 1)
            #     ax1.plot(t, rE2, 'C3')
            #     ax1.plot(t, rS2, 'C0')
            #     ax1.plot(t, rP2, 'darkblue')
            #     ax1.plot(t, rN2, 'C1')
            #     ax1.plot(t, cGABA2, 'C2')

        ax.plot(freqs, amplitudes_s/amplitudes_s.max(), '.-', c=cols_s[j], ms=4*lw, label=f"b={bb:1.1f}")
        ax.plot(freqs, amplitudes_n/amplitudes_n.max(), '.-', c=cols_n[j], ms=4*lw, label=f"b={bb:1.1f}")

    ax.set(ylim=[0, 1.1], ylabel='signal (norm)', xlabel='stimulus freq. (Hz)', yticks=[0, 1], xticks=[0, 5, 10, 15])
    # ax.legend(['NDNF', 'SOM'], title='stimulus to', loc='best')
    # ax.set(ylim=[0, 1.1], xlabel='stim. freq. (Hz)', title='stim to NDNF')
    # ax[0].legend(loc='best', fontsize=7, frameon=False, handlelength=2)
    # ax[1].legend(loc='best', fontsize=7, frameon=False, handlelength=2)

    if save:
        fig.savefig('../results/figs/Naumann23_draft1/exp3-1_freq-pref.pdf', dpi=300)
        plt.close(fig)


def exp302_transient_signals(reduced=False, mean_pop=True, w_hetero=False, pre_inh=True, save=False, noise=0):
    """
    Experiment2: Study transmission of transient signal by NDNF and SOM.
    """

    # define parameter dictionaries
    N_cells, w_mean, conn_prob, bg_inputs, taus = mb.get_default_params(flag_mean_pop=mean_pop)

    if reduced: # remove recurrence from model for reduced variant 
        w_mean['EP'], w_mean['PE'], w_mean['SE'] = 0, 0, 0

    # increase NDNF-dendrite inhibition
    wDNs = [w_mean['DN'], 0.8]      

    # TODO: remove
    # w_mean.update(dict(SV=0.5, PV=0.2, PN=0.3, VN=0.2))
    # w_mean.update(dict(SV=0.4, PV=0.2, PN=0.3, VN=0.2, DE=0.2))

    # simulation paramters
    dur = 5000
    dt = 1
    nt = int(dur/dt)

    stim_durs = (np.array([10, 20, 50, 100, 200, 500, 1000])*dt).astype(int)
    ts = int(1000*dt)
    amp = 1.5

    amplitudes_n = np.zeros(len(stim_durs))
    amplitudes_s = np.zeros(len(stim_durs))

    dpi = 300 if save else 300
    fig, ax = plt.subplots(2, 2, figsize=(2.75, 2.1), gridspec_kw=dict(right=0.97, top=0.95, bottom=0.27, left=0.2, wspace=0.15, hspace=0.15),
                             sharex=True, sharey=True, dpi=dpi)
    cols = sns.color_palette("flare", n_colors=len(stim_durs))

    for k, pre_inh in enumerate([True, False]):

        print(f"pre inh = {pre_inh}")

        for j, wDN in enumerate([0.4, 0.8]):

            # change wDN parameter
            w_mean['DN'] = wDN
            model = mb.NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_w_hetero=w_hetero, flag_pre_inh=pre_inh)

            for i, sdur in enumerate(stim_durs):

                xff_null = np.zeros(nt)
                xff_stim = xff_null.copy()
                xff_stim[ts:ts+sdur] = amp
                
                # simulate with sine input to SOM
                xFF = get_null_ff_input_arrays(nt, N_cells)
                xFF['S'] = np.tile(xff_stim, [N_cells['S'], 1]).T
                xFF['N'] = np.tile(xff_null, [N_cells['N'], 1]).T
                t, rE1, rD1, rS1, rN1, rP1, rV1, p1, cGABA1, other1 = model.run(dur, xFF, dt=dt, p0=0.5, calc_bg_input=True, noise=noise)

                # simulate with sine input to NDNF
                xFF = get_null_ff_input_arrays(nt, N_cells)
                xFF['S'] = np.tile(xff_null, [N_cells['S'], 1]).T
                xFF['N'] = np.tile(xff_stim, [N_cells['N'], 1]).T
                t, rE2, rD2, rS2, rN2, rP2, rV2, p2, cGABA2, other2 = model.run(dur, xFF, dt=dt, p0=0.5, calc_bg_input=True, noise=noise)

                bl1 = np.mean(rE1[500:ts])
                bl2 = np.mean(rE2[500:ts])
                amplitudes_s[i] = (np.mean(rE1[ts:ts+sdur]-bl1))
                amplitudes_n[i] = (np.mean(rE2[ts:ts+sdur]-bl2))

            ax[j, k].plot(np.arange(len(stim_durs)), amplitudes_n, '.-', c=cNDNF, label='NDNF', lw=lw, ms=4*lw)
            ax[j, k].plot(np.arange(len(stim_durs)), amplitudes_s, '.-', c=cSOM, label='SOM', lw=lw, ms=4*lw)
            ax[j, k].hlines(0, 0, len(stim_durs)-1, ls='--', color='k', zorder=-1, lw=1)
            ax[j, k].set(xticks=np.arange(len(stim_durs)), ylim=[-0.55, 0.55], yticks=[0.5, 0, -0.5])
            ax[j, 0].set(ylabel=r'$\Delta$ PC act.')
        ax[1, k].set(xlabel='stim. dur. (ms)')
        ax[1, k].set_xticklabels(stim_durs, rotation=45, ha='right', rotation_mode="anchor")

    if save:
        fig.savefig('../results/figs/Naumann23_draft1/exp3-2_transient-input.pdf', dpi=300)
        plt.close(fig)


def exp302a_transient_signals_ex(reduced=False, mean_pop=True, w_hetero=False, pre_inh=True, save=False, noise=0, wDN=0.4):
    """
    Experiment2: Study transmission of transient signal by NDNF and SOM.
    """

    # define parameter dictionaries
    N_cells, w_mean, conn_prob, bg_inputs, taus = mb.get_default_params(flag_mean_pop=mean_pop)

    if reduced: # remove recurrence from model for reduced variant 
        w_mean['EP'], w_mean['PE'], w_mean['SE'] = 0, 0, 0

    # increase NDNF-dendrite inhibition
    w_mean['DN'] = wDN

    # TODO: remove
    # w_mean.update(dict(SV=0.5, PV=0.2, PN=0.3, VN=0.2))
    # w_mean.update(dict(SV=0.4, PV=0.2, PN=0.3, VN=0.2, DE=0.2))

    # simulation paramters
    dur = 4000
    dt = 1
    nt = int(dur/dt)

    stim_durs = (np.array([100, 1000])*dt).astype(int)
    ts = int(1000*dt)
    amp = 1.5

    amplitudes_n = np.zeros(len(stim_durs))
    amplitudes_s = np.zeros(len(stim_durs))

    dpi = 300 if save else 300
    fig, ax = plt.subplots(3, 1, figsize=(1.5, 1.5), gridspec_kw=dict(right=0.97, top=0.95, bottom=0.3, left=0.25, wspace=0.15, hspace=0.15, height_ratios=[1, 1, 1]),
                             sharex=True, sharey=False, dpi=dpi)
    fig2, ax2 = plt.subplots(1, 1, dpi=300, figsize=(1.5, 0.9), sharex=True, sharey=True, gridspec_kw=dict(left=0.25, right=0.97))
    cols = sns.color_palette("flare", n_colors=len(stim_durs))

    model = mb.NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_w_hetero=w_hetero, flag_pre_inh=pre_inh)

    alphas = [1, 1]

    for i, sdur in enumerate(stim_durs):

        xff_null = np.zeros(nt)
        xff_stim = xff_null.copy()
        xff_stim[ts:ts+sdur] = amp
        
        # simulate with input to SOM
        xFF = get_null_ff_input_arrays(nt, N_cells)
        xFF['S'] = np.tile(xff_stim, [N_cells['S'], 1]).T
        xFF['N'] = np.tile(xff_null, [N_cells['N'], 1]).T
        t, rE1, rD1, rS1, rN1, rP1, rV1, p1, cGABA1, other1 = model.run(dur, xFF, dt=dt, p0=0.5, calc_bg_input=True, noise=noise, monitor_dend_inh=True)

        # simulate with input to NDNF
        xFF = get_null_ff_input_arrays(nt, N_cells)
        xFF['S'] = np.tile(xff_null, [N_cells['S'], 1]).T
        xFF['N'] = np.tile(xff_stim, [N_cells['N'], 1]).T
        t, rE2, rD2, rS2, rN2, rP2, rV2, p2, cGABA2, other2 = model.run(dur, xFF, dt=dt, p0=0.5, calc_bg_input=True, noise=noise, monitor_dend_inh=True)

        bl2 = np.mean(rE2[500:ts])
        amplitude = (np.mean(rE2[ts:ts+sdur]-bl2))
        print(f"stim dur = {sdur}, amplitude = {amplitude:1.3f}")

        # ax[0].plot(t/1000, xFF['N'][:, 0], c='k', lw=1, alpha=alphas[i])
        ax[0].plot(t/1000, np.mean(rN2, axis=1), c=cNDNF, lw=1, alpha=alphas[i])
        ax[0].plot(t/1000, np.mean(rS2, axis=1), c=cSOM, lw=1, alpha=alphas[i])
        ax[0].plot(t/1000, np.mean(rP2, axis=1), c=cPV, lw=1, alpha=alphas[i])
        # ax[2].plot(t/1000, np.mean(rD2, axis=1), c='k', lw=1, alpha=alphas[i])
        # ax[2].plot(t/1000, p2, c=cpi, lw=1, alpha=alphas[i])
        mean_inh_NDNF = np.mean(np.array(other2['dend_inh_NDNF']), axis=1)
        mean_inh_SOM = np.mean(np.array(other2['dend_inh_SOM']), axis=1)
        mean_inh_PV = np.mean(np.array(other2['soma_inh_PV']), axis=1)
        ax[1].plot(t/1000, mean_inh_NDNF-np.mean(mean_inh_NDNF[:ts]), c=cNDNF, lw=1, alpha=alphas[i], ls='--')
        ax[1].plot(t/1000, mean_inh_SOM-np.mean(mean_inh_SOM[:ts]), c=cSOM, lw=1, alpha=alphas[i], ls='--')
        ax[1].plot(t/1000, mean_inh_PV-np.mean(mean_inh_PV[:ts]), c=cPV, lw=1, alpha=alphas[i], ls='--')
        ax[-1].plot(t/1000, np.mean(rE2, axis=1)-np.mean(rE2[:ts]), c=cPC, lw=1, alpha=alphas[i])

        # bl1 = np.mean(rE1[500:ts])
        # bl2 = np.mean(rE2[500:ts])
        # amplitudes_s[i] = (np.mean(rE1[ts:ts+sdur]-bl1))
        # amplitudes_n[i] = (np.mean(rE2[ts:ts+sdur]-bl2))

    # ax[j, k].plot(np.arange(len(stim_durs)), amplitudes_n, '.-', c=cNDNF, label='NDNF', lw=lw, ms=4*lw)
    # ax[j, k].plot(np.arange(len(stim_durs)), amplitudes_s, '.-', c=cSOM, label='SOM', lw=lw, ms=4*lw)
    # ax[j, k].hlines(0, 0, len(stim_durs)-1, ls='--', color='k', zorder=-1, lw=1)
    # ax[j, k].set(xticks=np.arange(len(stim_durs)), ylim=[-0.55, 0.55], yticks=[0.5, 0, -0.5])
    # ax[j, 0].set(ylabel=r'$\Delta$ PC act.')

        ax[-1].set(xlabel='time (s)', ylim=[-0.35, 0.35], yticks=[-0.2, 0, 0.2], ylabel=r'$\Delta$ PC act.')
        # ax[1, k].set_xticklabels(stim_durs, rotation=45, ha='right', rotation_mode="anchor")


        # plot change in dendritic and somatic inhibition

        dend_inh_SOM = np.array(other2['dend_inh_SOM']).mean(axis=1)
        dend_inh_NDNF = np.array(other2['dend_inh_NDNF']).mean(axis=1)
        soma_inh_PV = np.array(other2['soma_inh_PV']).mean(axis=1)

        ddi_SOM = np.mean(dend_inh_SOM[ts:ts+sdur])-np.mean(dend_inh_SOM[:ts])
        ddi_NDNF = np.mean(dend_inh_NDNF[ts:ts+sdur])-np.mean(dend_inh_NDNF[:ts])
        dsi_PV = np.mean(soma_inh_PV[ts:ts+sdur])-np.mean(soma_inh_PV[:ts])
        ax2.bar(i*1.3-0.3, ddi_NDNF, facecolor='none', edgecolor=cNDNF, hatch='/////', width=0.2, label='NDNF' if i==0 else None)
        ax2.bar(i*1.3-0.1, ddi_SOM, facecolor='none', edgecolor=cSOM, hatch='/////', width=0.2, label='SOM' if i==0 else None)
        ax2.bar(i*1.3+0.1, dsi_PV, facecolor='none', edgecolor=cPV, hatch='/////', width=0.2, label='PV' if i==0 else None)
        ax2.bar(i*1.3+0.3, ddi_SOM+ddi_NDNF+dsi_PV, facecolor='none', edgecolor='silver', hatch='/////', width=0.2)
        ax2.hlines(0, -0.5, 1.8, color='k', lw=1)

        ax2.set(ylabel=r'$\Delta$ inh.', xticks=[], ylim=[-0.6, 1.1])
        ax2.spines['bottom'].set_visible(False)


            # ax2.bar(i+0.2, ddi_SOM+ddi_NDNF, facecolor='none', edgecolor='silver', hatch='/////', width=0.2, label='sum' if i==0 else None)

    if save:
        wDN_str = str(wDN).replace('.', 'p')
        # fig.savefig('../results/figs/Naumann23_draft1/exp3-2_transient-input.pdf', dpi=300)
        fig2.savefig(f"../results/figs/Naumann23_draft1/exp3-3_transient-input_inh-change_{wDN_str}.pdf", dpi=300)
        plt.close(fig2)


def exp303_cancelling_input_TD_BU():
    #TODO: cancelling top-down and bottom-up input with SOM and NDNF, respectively
    pass


def exp304_transient_effects(mean_pop=True, w_hetero=False, pre_inh=True, noise=0.0, reduced=False, save=False):
    #TODO: stimuli to NDNF take longer to have effect, in the mean time other things can happen
    """
    Experiment4: test if circuit can have transient behaviour. When NDNFs (+others) receive some input,
                 there is a transient window of dynamics before NDNFs change the ciruit dynamics.
    - give some longer input to NDNFs
    - test circuit response/dynamics for some input stimulus early and late during NDNF input
    """

    # define parameter dictionaries
    N_cells, w_mean, conn_prob, bg_inputs, taus = mb.get_default_params(flag_mean_pop=mean_pop)

    if reduced: # remove recurrence from model for reduced variant 
        w_mean['EP'], w_mean['PE'], w_mean['SE'] = 0, 0, 0

    # increase NDNF-dendrite inhibition
    w_mean['DS'] = 0.8 # so SOM-dend inhibition dominates over SOM-NDNF-dend disinhibition

    # instantiate model
    model = mb.NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_w_hetero=w_hetero,
                            flag_pre_inh=pre_inh)

    # simulation paramters
    dur = 5000
    dt = 1
    nt = int(dur/dt)

    # stimulation
    xFF = get_null_ff_input_arrays(nt, N_cells)
    xFF['N'][1000:4000] = 0.6  # long constant stimulus to NDNF
    xsine = np.sin(np.arange(0, 0.5, 0.001)*5*np.pi*2)*1  # 500ms long sine wave
    ts1, te1, ts2, te2 = 1000, 1500, 3500, 4000
    xFF['S'][ts1:te1] = np.tile(xsine, [N_cells['S'], 1]).T  # early sine input to SOM
    xFF['S'][ts2:te2] = np.tile(xsine, [N_cells['S'], 1]).T  # late sine input to SOM

    # simulate
    t, rE, rD, rS, rN, rP, rV, p, cGABA, other = model.run(dur, xFF, dt=dt, p0=0.5, noise=noise)

    # print(np.corrcoef(np.mean(rE[ts1:te1], axis=1), xsine)[0, 1])
    # print(np.corrcoef(np.mean(rE[ts2:te2], axis=1), xsine)[0, 1])

    sh = 35 # shift signals relative to rate to account for delay from integration
    print(f"first signal: {quantify_signals([xsine], np.mean(rE[ts1+sh:te1+sh], axis=1), bias=True)[0]:1.3f}")
    print(f"second signal: {quantify_signals([xsine], np.mean(rE[ts2+sh:te2+sh], axis=1), bias=True)[0]:1.3f}")

    # plot
    dpi = 300 if save else 120
    fig, ax = plt.subplots(5, 1, dpi=dpi, gridspec_kw=dict(hspace=0.4, wspace=0.5, right=0.95, top=0.95, bottom=0.13, left=0.2),
                                 figsize=(6, 6.22))
    # cols = sns.color_palette("flare", n_colors=len(stim_durs))
    ax[4].plot(t/1000, rE, c=cPC, lw=2)
    ax[2].plot(t/1000, rD, c='k', lw=2)
    ax[1].plot(t/1000, rS, c=cSOM, lw=2)
    ax[0].plot(t/1000, rN, c=cNDNF, lw=2)
    ax[3].plot(t/1000, rP, c=cPV, lw=2)
    # ax[5].plot(t/1000, p, c=cpi)
    # ax[0].hlines(2.4, 1, 4, color=cNDNF, alpha=0.2, lw=5)
    # ax[6].plot(t, p, c='C2', alpha=1)
    for i, label in enumerate(['NDNF', 'SOM', 'dend.', 'PV']):
        ax[i].set(ylabel=label, ylim=[0, 2.5], yticks=[0, 2], xticks=[])
        ax[i].spines['bottom'].set_visible(False)
    ax[-1].set(xlabel='time (s)', ylim=[0, 2.5], yticks=[0, 2], ylabel='PC', xticks=[0, 2, 4])

    ax[4].plot(np.arange(ts1+sh,te1+sh)/1000, xsine/3+2.1, c=cSOM, lw=2, ls='-')
    ax[4].plot(np.arange(ts2+sh,te2+sh)/1000, xsine/3+2.1, c=cSOM, lw=2, ls='-')
    # ax[1].plot(np.arange(ts1-600,te1-600)/1000, xsine/5+2, c=cSOM, lw=3, ls='-', alpha=0.2)
    # ax[1].plot(np.arange(ts2,te2)/1000, xsine/5+2.3, c=cSOM, lw=1, ls='-', alpha=0.2)

    if save:
        fig.savefig('../results/figs/cosyne-collection/exp3-4_transient-effect.png', dpi=300)
        plt.close(fig)


def make_sine(nt, freq, plot=False):
    t = np.arange(nt)/1000
    sine = (np.sin(2*np.pi*freq*t)+1)/2
    if plot:
        plt.figure(figsize=(3, 2), dpi=300)
        plt.plot(t, sine, lw=lw, c='k')
    return sine


def fft_signal_contribution(x, dt=1):

    xnorm = (x-np.mean(x))/np.std(x)

    sample_rate = 1000/dt
    N = len(x)
    yf = fft(xnorm)
    freq = fftfreq(int(N), 1/sample_rate)

    # fig, ax = plt.subplots(1, 2)
    # ax[0].plot(x)
    # ax[1].plot(freq[:N//2], np.abs(yf)[:N//2]/1000)
    # ax[1].set(xlim=[0, 20])
    perHz = int(N/sample_rate)

    return freq[:N//2], np.abs(yf)[:N//2]/1000, perHz


def signal_amplitude(x, tstart=500):

    x_use = x[tstart:]

    ind_peak = detect_peaks(x_use, mpd=5)
    ind_valley = detect_peaks(x_use, mpd=5, valley=True)
    n_vp = np.min([len(ind_peak), len(ind_valley)])

    ampls = x_use[ind_peak[:n_vp]]-x_use[ind_valley[:n_vp]]
    return np.mean(ampls)


if __name__ in "__main__":

    # Fig 5 C: frequency preference
    # exp301_frequency_preference(reduced=False, save=True, mean_pop=False, w_hetero=True, noise=0.1, pre_inh=False)

    # Fig 5 D&E: responses of PC to SOM/NDNF stimulation depend on parameters and stimulus duration
    # exp302_transient_signals(reduced=False, save=True, mean_pop=False, w_hetero=True, noise=0.1)
    exp302a_transient_signals_ex(reduced=False, save=True, mean_pop=False, w_hetero=True, noise=0.1, pre_inh=True, wDN=0.4)
    exp302a_transient_signals_ex(reduced=False, save=True, mean_pop=False, w_hetero=True, noise=0.1, pre_inh=True, wDN=0.8)

    # old stuff
    # exp304_transient_effects(reduced=False, pre_inh=True, mean_pop=False, w_hetero=True, noise=0.1, save=False)
    # make_sine(1000, 4, plot=True)

    plt.show()
