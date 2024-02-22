"""
Experiments 1: NDNF interneurons as part of the microcircuit.
- paired recordings to show slow NDNF-mediated inhibition and unidirectional SOM-NDNF inhibition
- 'imaging' of SOM boutons shows presynaptic inhibition mediated by NDNF interneurons
- layer-specificity: only the outputs of SOMs in layer 1 are affected, not their outputs in deeper layers
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
plt.style.use('pretty')
import matplotlib as mpl
lw = mpl.rcParams['lines.linewidth']

import model_base as mb
from experiments import get_null_ff_input_arrays, get_model_colours, plot_violin

cPC, cPV, cSOM, cNDNF, cVIP, cpi = get_model_colours()

DPI = 300

def exp101_paired_recordings_invitro(dur=1000, dt=1, w_hetero=False, mean_pop=True, pre_inh=True, noise=0, save=False):
    """
    Experiment1: paired "in vitro" recordings and plot.
    - stimulate NDNF and SOM, record from PC, SOM and NDNF
    - "in vitro" means all cells have 0 baseline activity
    - paired recordings means the ingoing currents to each cell

    Parameters
    - dur: length of experiment
    - dt: time step
    - ...
    """
    # TODO: complete list of parameters

    # simulation paramters
    nt = int(dur / dt)
    t = np.arange(0, dur, dt)
    t0 = 100
    amp = 3

    # create figure
    dpi = 300 if save else DPI
    fig, ax = plt.subplots(2, 2, figsize=(2, 1.5), dpi=dpi, sharex=True, sharey='row',
                           gridspec_kw={'right': 0.93, 'bottom': 0.24, 'left': 0.22, 'top': 0.95, 'wspace': 0.3})
    
    fig2, ax2 = plt.subplots(1, 1, figsize=(1.8, 1.15), dpi=dpi, sharex=True, sharey='row',
                           gridspec_kw={'right': 0.95, 'bottom': 0.33, 'left': 0.25})

    # get default parameters
    N_cells, w_mean, conn_prob, bg_inputs, taus = mb.get_default_params(flag_mean_pop=mean_pop)

    # increase NDNF->dendrite inhibition so the effect is comparable to SOM->dendrite (visually in timescale plot)
    # w_mean['DN'] = 1.  # not necessary?

    # labels
    labelz = ['SOM', 'NDNF']

    # stimulate SOM and NDNF, respectively
    for i, cell in enumerate(['S', 'N']):

        # array of FF input
        xFF = get_null_ff_input_arrays(nt, N_cells)
        xFF[cell][:, :] = amp * np.tile(np.exp(-(t - t0) / 50) * np.heaviside(t - t0, 1), (N_cells[cell], 1)).T
        # xFF[cell][50:150, :] = 2

        # create model and run
        model = mb.NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_w_hetero=w_hetero,
                                flag_pre_inh=pre_inh, gamma=1)
        t, rE, rD, rS, rN, rP, rV, p, cGABA, other = model.run(dur, xFF, dt=dt, init_noise=0, noise=noise, 
                                                               rE0=0, rD0=1, rN0=0, rS0=0, rP0=0, monitor_currents=True)
        print('bg inputs:', model.Xbg)
        # note: dendritic activity is set to 1 so that the inhibition by SOM and NDNF shows in the soma

        # plotting and labels
        # ax[0, i].plot(t[1:], other['curr_rE'], c=cPC, alpha=0.1)
        # ax[1, i].plot(t[1:], other['curr_rS'], c=cSOM, alpha=0.1)
        # ax[2, i].plot(t[1:], other['curr_rN'], c=cNDNF, alpha=0.1)
        ax[1, i].plot(t[1:], -np.mean(other['curr_rS'], axis=1), c=cSOM, lw=2)
        ax[0, i].plot(t[1:], -np.mean(other['curr_rN'], axis=1), c=cNDNF, lw=2)
        ax[1, i].set(xlabel='time (ms)', ylim=[-0.1, 3])
        mean_act = np.mean(other['curr_rE'], axis=1)
        ax2.plot(t[1:]/1000, -mean_act, c=eval('c'+labelz[i]), label=f'{labelz[i]} inh.', lw=1)


    # ax[0, 0].set(ylim=[-1, 1], ylabel='curr. (au)')
    ax[0, 0].set(ylim=[-3, 3], ylabel='curr. (au)', yticks=[-2, 0, 2], xlim=[0, 500])
    ax[1, 0].set(ylim=[-3, 3], ylabel='curr. (au)', yticks=[-2, 0, 2], xlim=[0, 500])
    # ax2[0].set(ylim=[-0.8, 0.1])
    ax2.legend(loc=(0.35, 0.56), handlelength=1, frameon=False, fontsize=8)
    ax2.set(xlabel='time (s)', ylim=[-0.05, 0.8], xticks=[0, 1], ylabel='PC curr. (au)')

    if save:
        fig.savefig('../results/figs/Naumann23_draft1/exp1-1_paired-recordings1.pdf', dpi=300)
        fig2.savefig('../results/figs/Naumann23_draft1/exp1-1_timescales.pdf', dpi=300)
        plt.close(fig)


def exp102_preinh_bouton_imaging(dur=2000, ts=200, te=500, dt=1, stim_NDNF=1.5, w_hetero=True, mean_pop=False, pre_inh=True, noise=0.2, save=False):
    """
    Experiment2: Image SOM bouton in response to stimulation of NDNF interneurons.

    Parameters
    - dur: duration of experiment (ms)
    - ts: start of NDNF stimulation
    - te: end of NDNF stimulation
    - dt: integration time step (ms)
    - stim_NDNF: strength of NDNF stimulation
    - noise: level of white noise added to neural activity
    - flag_w_hetero: whether to add heterogeneity to weight matrices
    - mean_pop: if true, simulate only one neuron (mean) per population
    """

    # define parameter dictionaries
    N_cells, w_mean, conn_prob, bg_inputs, taus = mb.get_default_params(flag_mean_pop=mean_pop)

    # instantiate model
    model = mb.NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_w_hetero=w_hetero,
                           flag_pre_inh=pre_inh)

    # simulation paramters
    nt = int(dur/dt)

    # generate inputs
    xFF = get_null_ff_input_arrays(nt, N_cells)
    xFF['N'][ts:te] = stim_NDNF

    # run model
    t, rE, rD, rS, rN, rP, rV, p, cGABA, other = model.run(dur, xFF, init_noise=0.1, noise=noise, dt=dt, monitor_boutons=True,
                                                           monitor_currents=True)
    # TODO: add init_noise as parameter to the function?

    # plotting
    # --------
    # 3 different plots here: an overview plot, bouton imaging + quantification and only bouton imaging

    # plot 1: response of all neurons to NDNF stimulation
    dpi = 300 if save else DPI
    fig, ax = plt.subplots(6, 1, figsize=(4, 5), dpi=dpi, sharex=True)
    ax[4].plot(t, rE, c=cPC, alpha=0.5)
    ax[3].plot(t, rD, c='k', alpha=0.5)
    ax[1].plot(t, rS, c=cSOM, alpha=0.5)
    ax[0].plot(t, rN, c=cNDNF, alpha=0.5)
    ax[2].plot(t, rP, c=cPV, alpha=0.5)
    ax[5].plot(t, p, c=cpi, alpha=1)
    for i, label in enumerate(['PC', 'dend.', 'SOM', 'NDNF', 'PV']):
        ax[i].set(ylabel=label, ylim=[0, 3])
    ax[5].set(ylabel='p', ylim=[0, 1], xlabel='time (s)')

    # plot 2: monitoring SOM boutons
    fig2, ax2 = plt.subplots(1, 1, figsize=(2.2, 1.6), dpi=dpi, gridspec_kw={'left':0.22, 'right':0.9, 'bottom':0.23})
    boutons = np.array(other['boutons_SOM'])
    boutons_nonzero = boutons[:, np.mean(boutons, axis=0) > 0]
    cm = ax2.pcolormesh(boutons_nonzero.T, cmap='Blues', vmin=0) #, vmax=0.15)
    cb = plt.colorbar(cm, ticks=[0, 0.5])
    cb.set_label('act. (au)', rotation=0, labelpad=-30, y=1.15)
    # cb.ax.get_yaxis().labelpad = 15
    ax2.set(xlabel='time (ms)', ylabel='# bouton (SOM out)', yticks=[0, (len(boutons_nonzero.T)//50)*50],
            xticks=[0, 1000, 2000], xticklabels=[0, 1, 2])

    # plot 3: quantification of monitoring SOM boutons
    fig3, ax3 = plt.subplots(1, 1, figsize=(2.5, 2), dpi=dpi, gridspec_kw={'left': 0.25, 'right':0.9, 'bottom':0.2})
    boutons_NDNFact = np.mean(boutons_nonzero[ts:te+200], axis=0)
    boutons_cntrl = np.mean(boutons_nonzero[0:ts], axis=0)
    plot_violin(ax3, 0, boutons_cntrl, color=cSOM)
    plot_violin(ax3, 1, boutons_NDNFact, color='#E9B86F')
    ax3.set(xlim=[-0.5, 1.5], xticks=[0, 1], xticklabels=['ctrl', 'NDNF act.'], ylim=[0, 0.6], yticks=[0, 0.5],
            ylabel='SOM bouton act.')
    
    if save:
        # fig.savefig('../results/figs/cosyne-collection/exp1-2_preinh-allneurons.png', dpi=300)
        fig2.savefig('../results/figs/Naumann23_draft1/exp1-2_preinh-boutons-all.pdf', dpi=300)
        # fig3.savefig('../results/figs/cosyne-collection/exp1-2_preinh-boutons-violin.png', dpi=300)
        [plt.close(ff) for ff in [fig, fig2, fig3]]


def exp103_layer_specificity(dur=1500, dt=1, w_hetero=False, mean_pop=True, noise=0.0, pre_inh=True, save=False):
    """
    Experiment3: Vary input to NDNF interneurons, monitor NDNF- and SOM-mediated dendritic inhibition and their activity.

    Parameters
    - dur: duration of experiment (ms)
    - dt: integration time step (ms)
    - noise: level of white noise added to neural activity
    - flag_w_hetero: whether to add heterogeneity to weight matrices
    - save: if it's a string, name of the saved file, else if False nothing is saved
    """

    # extract number of timesteps
    nt = int(dur / dt)

    # get default parameters
    N_cells, w_mean, conn_prob, bg_inputs, taus = mb.get_default_params(flag_mean_pop=mean_pop)

    # TODO: remove
    # w_mean.update(dict(SV=0.4, PV=0.2, PN=0.3, VN=0.2, DE=0.2))
    # w_mean.update(dict(DN=0.4))
    # w_mean['NS'] = 1.5

    # mb.plot_w_mean(w_mean)

    # array for varying NDNF input
    ndnf_input = np.arange(-1, 1, 0.05)
    ninput = len(ndnf_input)

    # empty arrays for recording stuff
    rS_inh_record = np.zeros(ninput)
    rN_inh_record = np.zeros(ninput)
    rS_record = np.zeros((ninput, N_cells['S']))
    rN_record = np.zeros((ninput, N_cells['N']))
    # rV_record = np.zeros((ninput, N_cells['V'])) # TODO: remove
    cGABA_record = np.zeros(ninput)
    p_record = np.zeros(ninput)

    for i, I_activate in enumerate(ndnf_input):

        # create input (stimulation of NDNF)
        xFF = get_null_ff_input_arrays(nt, N_cells)
        xFF['N'][:, :] = I_activate

        # instantiate and run model
        model = mb.NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_w_hetero=w_hetero,
                                flag_pre_inh=pre_inh)
        t, rE, rD, rS, rN, rP, rV, p, cGABA, other = model.run(dur, xFF, dt=dt, init_noise=0, monitor_dend_inh=True,
                                                               noise=noise)
        print('bg inputs:', model.Xbg)
        # TODO: add init_noise?

        # save stuff
        rS_record[i] = rS[-1]
        rN_record[i] = rN[-1]
        # rV_record[i] = rV[-1] #TODO: remove
        rS_inh_record[i] = np.mean(np.array(other['dend_inh_SOM'][-1]))
        rN_inh_record[i] = np.mean(np.array(other['dend_inh_NDNF'][-1]))
        cGABA_record[i] = np.mean(cGABA[-1])
        p_record[i] = p[-1]

    # plotting
    dpi = 300 if save else DPI
    fig, ax = plt.subplots(2, 1, figsize=(1.6, 2.5), dpi=dpi, gridspec_kw={'left': 0.22, 'bottom': 0.15, 'top': 0.95,
                                                                           'right': 0.95, 'hspace': 0.2,
                                                                           'height_ratios': [1, 1]}, sharex=True)
    ax[1].plot(ndnf_input, rS_inh_record, c=cSOM, ls='--', lw=lw)
    ax[1].plot(ndnf_input, rN_inh_record, c=cNDNF, ls='--', lw=lw)
    ax[1].plot(ndnf_input, rS_inh_record+rN_inh_record, c='#978991', ls='-', lw=lw, zorder=-1)
    rSmu, rSstd = np.mean(rS_record, axis=1), np.std(rS_record, axis=1)
    rNmu, rNstd = np.mean(rN_record, axis=1), np.std(rN_record, axis=1)
    ax[0].plot(ndnf_input, rSmu, color=cSOM, lw=lw)
    ax[0].plot(ndnf_input, rNmu, color=cNDNF, lw=lw)
    # ax[0].plot(ndnf_input, np.mean(rV_record, axis=1), color=cVIP, lw=lw)  # TODO:remove
    ax[0].legend(['SOM', 'NDNF'], frameon=False, handlelength=1, loc=(0.05, 0.6), fontsize=8)
    # ax[1].fill_between(ndnf_input, rSmu-rSstd, rSmu+rSstd, color=cSOM, alpha=0.5)
    # ax[1].fill_between(ndnf_input, rNmu-rNstd, rNmu+rNstd, color=cNDNF, alpha=0.5)

    # labels etc
    ax[1].set(ylabel='dend. inh. (au)', ylim=[-0.05, 1.1], yticks=[0, 1], xlabel=r'$\Delta$ NDNF input')
    ax[0].set(ylabel='activity (au)', xlim=[-1, 1], ylim=[-0.1, 2.5],
              yticks=[0, 1, 2])

    # TODO: remove
    # fig2, ax2 = plt.subplots(2, 1, figsize=(2.1, 2.8), dpi=dpi, gridspec_kw={'left': 0.25, 'bottom': 0.15, 'top': 0.95,
    #                                                                        'right': 0.95,
    #                                                                        'height_ratios': [1, 1]}, sharex=True)
    # ax2[0].plot(ndnf_input, cGABA_record, c=cpi)
    # ax2[1].plot(ndnf_input, p_record, c=cpi)
    # ax2[0].set(ylabel='GABA conc. (au)')
    # ax2[1].set(ylabel='release p', xlabel='input to NDNF (au)')

    # saving
    if save:
        savename = '../results/figs/Naumann23_draft1/exp1-3_layer-specificity.pdf'
        if not pre_inh:
            savename = savename.replace('.pdf', '_no-preinh.pdf')
        fig.savefig(savename, dpi=300)
        # fig2.savefig('../results/figs/cosyne-collection/exp1-3_layer-specificity_GABA', dpi=300)
        plt.close(fig)


def exp103b_total_dendritic_inhibition(dur=1500, dt=1, w_hetero=False, mean_pop=True, noise=0.0, pre_inh=True, save=False):
    """
    Experiment3b: Vary input to NDNF interneurons and NDNF->dendrite weight, check how this affects total dendritic inhibition.

    Parameters
    - dur: duration of experiment (ms)
    - dt: integration time step (ms)
    - noise: level of white noise added to neural activity
    - flag_w_hetero: whether to add heterogeneity to weight matrices
    - save: if it's a string, name of the saved file, else if False nothing is saved
    """

    # extract number of timesteps
    nt = int(dur / dt)

    # get default parameters
    N_cells, w_mean, conn_prob, bg_inputs, taus = mb.get_default_params(flag_mean_pop=mean_pop)

    # array for varying NDNF input
    ndnf_input = np.arange(-1, 1.05, 0.1)
    weightsDN = np.arange(0, 0.9, 0.2)

    # TODO: remove
    # w_mean.update(dict(SV=0.4, PV=0.2, PN=0.3, VN=0.2, DE=0.2))

    # empty arrays for recording stuff
    rS_inh_record = np.zeros((len(ndnf_input), len(weightsDN)))
    rN_inh_record = np.zeros((len(ndnf_input), len(weightsDN)))

    # set up figure
    dpi = 300 if save else DPI
    fig, ax = plt.subplots(1, 1, figsize=(1.6, 1.5), dpi=dpi, gridspec_kw={'left': 0.22, 'bottom': 0.25, 'top': 0.95,
                                                                           'right': 0.95}, sharex=True)
    # fig2, ax2 = plt.subplots(1, 1, figsize=(1.6, 1.5), dpi=dpi, gridspec_kw={'left': 0.22, 'bottom': 0.25, 'top': 0.95,
                                                                        #    'right': 0.95}, sharex=True)
    cols = sns.color_palette(f"blend:{cSOM},{cNDNF}", n_colors=len(weightsDN))

    for j, wDN in enumerate(weightsDN):

        w_mean['DN'] = wDN
        print(f"NDNF/SOM dendritic inh: {w_mean['DN']/w_mean['DS']:1.2f}")

        # instantiate and run model
        # bg_inputs = {'E': 0.5, 'D': 1.9, 'N': 1.9, 'S': 0.7, 'P': 1.7, 'V': 1.5}
        bg_inputs = {'E': 0.5, 'D': 1.7, 'N': 1.9, 'S': 0.6, 'P': 1.4, 'V': 1.4}
        model = mb.NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_w_hetero=w_hetero,
                                flag_pre_inh=pre_inh)
        

        for i, I_activate in enumerate(ndnf_input):

            # create input (stimulation of NDNF)
            xFF = get_null_ff_input_arrays(nt, N_cells)
            xFF['N'][:, :] = I_activate

            t, rE, rD, rS, rN, rP, rV, p, cGABA, other = model.run(dur, xFF, dt=dt, init_noise=0, monitor_dend_inh=True,
                                                               noise=noise, calc_bg_input=False)
            # TODO: add init_noise?

            # save stuff
            rS_inh_record[i, j] = np.mean(np.array(other['dend_inh_SOM'][-1]))
            rN_inh_record[i, j] = np.mean(np.array(other['dend_inh_NDNF'][-1]))

        ax.plot(ndnf_input, rS_inh_record[:, j]+rN_inh_record[:, j], c=cols[j], ls='-', label=f"{wDN/w_mean['DS']:1.1f}", lw=lw)
    
        print(model.Xbg)

    ax.set(xlabel=r'$\Delta$ NDNF input', xticks=[-1, 0, 1], xlim=[-1, 1], ylim=[0, 2], yticks=[0, 1, 2], ylabel=r'$\Sigma$ dend. inh.')
    # ax.legend(loc=(1.01, 0.2), frameon=False, handlelength=1, title='N/S -> D')

    #TODO: remove
    # ax2.pcolormesh(ndnf_input, weightsDN, (rS_inh_record+rN_inh_record).T, cmap='coolwarm_r', vmin=0, vmax=2)

    # saving
    if save:
        savename = '../results/figs/Naumann23_draft1/exp1-3b_dendritic_inhibition.pdf'
        if not pre_inh:
            savename = savename.replace('.pdf', '_no-preinh.pdf')
        fig.savefig(savename, dpi=300)
        plt.close(fig) 


def exp103c_amplifcation_ndnf_inhibition(dur=1500, dt=1, w_hetero=False, mean_pop=True, noise=0.0, pre_inh=True, save=False):
    """
    Experiment3b: Vary input to NDNF interneurons and pre inh strength, check how this affects NDNF inhibition to dendrite.

    Parameters
    - dur: duration of experiment (ms)
    - dt: integration time step (ms)
    - noise: level of white noise added to neural activity
    - flag_w_hetero: whether to add heterogeneity to weight matrices
    - save: if it's a string, name of the saved file, else if False nothing is saved
    """

    # extract number of timesteps
    nt = int(dur / dt)

    # get default parameters
    N_cells, w_mean, conn_prob, bg_inputs, taus = mb.get_default_params(flag_mean_pop=mean_pop)

    # instantiate and run model
    model = mb.NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_w_hetero=w_hetero,
                            flag_pre_inh=pre_inh)

    # array for varying NDNF input
    ndnf_input = np.arange(-1, 1, 0.05)
    betas = np.linspace(0, 0.5, 2, endpoint=True)

    # empty arrays for recording stuff
    # rS_inh_record = np.zeros((len(ndnf_input), len(betas)))
    rN_inh_record = np.zeros((len(ndnf_input), len(betas)))

    # set up figure
    dpi = 300 if save else DPI
    fig, ax = plt.subplots(1, 1, figsize=(3, 3), dpi=dpi, gridspec_kw={'left': 0.22, 'bottom': 0.25, 'top': 0.95,
                                                                           'right': 0.95}, sharex=True)
    cols = sns.color_palette(f"dark:{cpi}", n_colors=len(betas))

    for j, bb in enumerate(betas):

        print(f"beta: {bb:1.1f}")

        model.b = bb

        for i, I_activate in enumerate(ndnf_input):

            # create input (stimulation of NDNF)
            xFF = get_null_ff_input_arrays(nt, N_cells)
            xFF['N'][:, :] = I_activate

            t, rE, rD, rS, rN, rP, rV, p, cGABA, other = model.run(dur, xFF, dt=dt, init_noise=0, monitor_dend_inh=True,
                                                               noise=noise)
            # TODO: add init_noise?

            # save stuff
            # rS_inh_record[i, j] = np.mean(np.array(other['dend_inh_SOM'][-1]))
            # rN_inh_record[i, j] = np.mean(np.array(other['dend_inh_NDNF'][-1]))
            rN_inh_record[i, j] = np.mean(rN[-1])
        print(model.Xbg)


        ax.plot(ndnf_input, rN_inh_record[:, j], c=cols[j], ls='-', label=f"{bb:1.1f}", lw=lw)
    
    ax.set(xlabel=r'$\Delta$ NDNF input', xticks=[-1, 0, 1], xlim=[-1, 1], ylim=[-0.1, 2.5], yticks=[0, 1, 2], ylabel='NDNF act. (au)')
    ax.legend(['no pre. inh.', 'pre. inh.'], loc=(0.05, 0.7))

    # saving
    if save:
        fig.savefig('../results/figs/cosyne-collection/exp1-3c_amplification_NDNFinh', dpi=300)
        plt.close(fig)


def exp104_motifs_SOM_PC(dur=2000, dt=1, w_hetero=False, mean_pop=True, pre_inh=True, noise=0, save=False):
    """
    Experiment4a: Measure inhibition from SOM to PC with active and inactive NDNF (i.e. with and without pre inh).

    Parameters
    - dur: length of experiment
    - dt: time step
    - ...
    """
    # TODO: complete list of parameters

    # simulation paramters
    nt = int(dur / dt)
    t = np.arange(0, dur, dt)
    t0 = 1100
    amp = 3

    # create figure
    dpi = 300 if save else DPI
    fig, ax = plt.subplots(1, 1, figsize=(1.2, 1), dpi=dpi, gridspec_kw={'right': 0.95, 'bottom': 0.1, 'left': 0.1, 'top': 0.95})
    
    # get default parameters
    N_cells, w_mean, conn_prob, bg_inputs, taus = mb.get_default_params(flag_mean_pop=mean_pop)

    # labels
    labelz = ['SOM', 'NDNF']

    # stimulate SOM and NDNF, respectively

    # array of FF input
    xFF = get_null_ff_input_arrays(nt, N_cells)
    xFF['S'][:, :] = amp * np.tile(np.exp(-(t - t0) / 50) * np.heaviside(t - t0, 1), (N_cells['S'], 1)).T
    # xFF[cell][50:150, :] = 2

    # create model and run
    model = mb.NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_w_hetero=w_hetero,
                            flag_pre_inh=pre_inh, gamma=1)
    
    t, rE, rD, rS, rN, rP, rV, p, cGABA, other = model.run(dur, xFF, dt=dt, init_noise=0, noise=noise, monitor_currents=True,
                                                            rP0=0, rN0=0, rE0=0, rS0=0, rV0=0,rD0=1,
                                                            calc_bg_input=True)
    print('bg inputs:', model.Xbg)

    # now run again but NDNFs are more active
    xFF['N'] += 1.5
    t, rE2, rD2, rS2, rN2, rP2, rV2, p2, cGABA2, other2 = model.run(dur, xFF, dt=dt, init_noise=0, noise=noise, monitor_currents=True,
                                                                    rP0=0, rN0=0, rE0=0, rS0=0, rV0=0,rD0=1,
                                                                    calc_bg_input=False)
    
    # note: dendritic activity is set to 1 so that the inhibition by SOM soma, all other neurons inactive by default

    curr_rE = np.mean(other['curr_rE'], axis=1)
    curr_rE2 = np.mean(other2['curr_rE'], axis=1)
    ts = 1000
    tplot = (t[ts+1:]-ts)/1000
    ax.plot(tplot, (curr_rE-np.mean(curr_rE[1000:1100]))[ts:], c=cPC, lw=1)
    ax.plot(tplot, (curr_rE2-np.mean(curr_rE2[1000:1100]))[ts:], c='#D29FA3', lw=1)
    ax.axis('off')

    # add scale bars    
    ax.add_patch(plt.Rectangle((0.8, -0.1), 0.2, 0.02, facecolor='k', edgecolor='k', lw=0))
    ax.text(0.9, -0.15, '200ms', ha='center', va='top', color='k', fontsize=8)  
    ax.add_patch(plt.Rectangle((0.05, -0.6), 0.02, 0.2, facecolor='k', edgecolor='k', lw=0))
    ax.text(0.035, -0.5, '0.2', ha='right', va='center', color='k', fontsize=8)  

    # add SOM activation patch
    ax.add_patch(plt.Rectangle((0.1, 0.05), 0.1, 0.05, facecolor=cSOM, lw=0, alpha=0.5))

    # plot activity of all cell types
    fig2, ax2 = plt.subplots(6, 1, dpi=150, figsize=(4, 4), sharex=True)
    ax2[0].plot(t/1000, np.mean(rE2, axis=1), c=cPC, lw=1)
    ax2[1].plot(t/1000, np.mean(rD2, axis=1), c='k', lw=1)
    ax2[2].plot(t/1000, np.mean(rS2, axis=1), c=cSOM, lw=1)
    ax2[3].plot(t/1000, np.mean(rN2, axis=1), c=cNDNF, lw=1)
    ax2[4].plot(t/1000, np.mean(rP2, axis=1), c=cPV, lw=1)
    ax2[5].plot(t/1000, p2, c=cpi, lw=1)

    if save:
        fig.savefig('../results/figs/Naumann23_draft1/exp1-4_motif_SOM-PC.pdf', dpi=300)
        plt.close(fig)
        plt.close(fig2)


def exp104_motifs_SOM_NDNF(dur=2000, dt=1, w_hetero=False, mean_pop=True, pre_inh=True, noise=0, save=False):
    """
    Experiment4: Experiment4a: Measure inhibition from SOM to NDNF with active and inactive NDNF (i.e. with and without pre inh).

    Parameters
    - dur: length of experiment
    - dt: time step
    - ...
    """
    # TODO: complete list of parameters

    # simulation paramters
    nt = int(dur / dt)
    t = np.arange(0, dur, dt)
    t0 = 1100
    amp = 3

    # create figure
    dpi = 300 if save else DPI
    fig, ax = plt.subplots(1, 1, figsize=(1.2, 1), dpi=dpi, gridspec_kw={'right': 0.95, 'bottom': 0.1, 'left': 0.1, 'top': 0.95})
    
    # get default parameters
    N_cells, w_mean, conn_prob, bg_inputs, taus = mb.get_default_params(flag_mean_pop=mean_pop)

    # labels
    labelz = ['SOM', 'NDNF']

    # stimulate SOM and NDNF, respectively

    # array of FF input
    xFF = get_null_ff_input_arrays(nt, N_cells)
    xFF['S'][:, :] = amp * np.tile(np.exp(-(t - t0) / 50) * np.heaviside(t - t0, 1), (N_cells['S'], 1)).T
    # xFF[cell][50:150, :] = 2

    # create model and run
    model = mb.NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_w_hetero=w_hetero,
                            flag_pre_inh=pre_inh, gamma=1)
    
    t, rE, rD, rS, rN, rP, rV, p, cGABA, other = model.run(dur, xFF, dt=dt, init_noise=0, noise=noise, monitor_currents=True,
                                                            rP0=0, rN0=0, rE0=0, rS0=0, rV0=0,rD0=1,
                                                            calc_bg_input=True)
    print('bg inputs:', model.Xbg)

    # now run again but NDNFs are more active
    xFF['N'] += 1.5
    t, rE2, rD2, rS2, rN2, rP2, rV2, p2, cGABA2, other2 = model.run(dur, xFF, dt=dt, init_noise=0, noise=noise, monitor_currents=True,
                                                                    rP0=0, rN0=0, rE0=0, rS0=0, rV0=0,rD0=1,
                                                                    calc_bg_input=False)
    
    # note: dendritic activity is set to 1 so that the inhibition by SOM soma, all other neurons inactive by default

    curr_rN = np.mean(other['curr_rN'], axis=1)
    curr_rN2 = np.mean(other2['curr_rN'], axis=1)
    ts = 1000
    tplot = (t[ts+1:]-ts)/1000
    ax.plot(tplot, (curr_rN-np.mean(curr_rN[1000:1100]))[ts:], c=cNDNF, lw=1)
    ax.plot(tplot, (curr_rN2-np.mean(curr_rN2[1000:1100]))[ts:], c='#EAC8B7', lw=1)
    ax.axis('off')

    # add scale bars    
    ax.add_patch(plt.Rectangle((0.8, -0.15), 0.2, 0.03, facecolor='k', edgecolor='k', lw=0))
    ax.text(0.9, -0.22, '200ms', ha='center', va='top', color='k', fontsize=8)  
    ax.add_patch(plt.Rectangle((0.05, -0.9), 0.02, 0.3, facecolor='k', edgecolor='k', lw=0))
    ax.text(0.035, -0.75, '0.3', ha='right', va='center', color='k', fontsize=8)  

    # add SOM activation patch
    ax.add_patch(plt.Rectangle((0.1, 0.09), 0.1, 0.1, facecolor=cSOM, lw=0, alpha=0.5))

    # plot activity of all cell types
    fig2, ax2 = plt.subplots(6, 1, dpi=150, figsize=(4, 4), sharex=True)
    ax2[0].plot(t/1000, np.mean(rE2, axis=1), c=cPC, lw=1)
    ax2[1].plot(t/1000, np.mean(rD2, axis=1), c='k', lw=1)
    ax2[2].plot(t/1000, np.mean(rS2, axis=1), c=cSOM, lw=1)
    ax2[3].plot(t/1000, np.mean(rN2, axis=1), c=cNDNF, lw=1)
    ax2[4].plot(t/1000, np.mean(rP2, axis=1), c=cPV, lw=1)
    ax2[4].plot(t/1000, np.mean(rV2, axis=1), c=cVIP, lw=1)
    ax2[5].plot(t/1000, p2, c=cpi, lw=1)

    if save:
        fig.savefig('../results/figs/Naumann23_draft1/exp1-4_motif_SOM-NDNF.pdf', dpi=300)
        plt.close(fig)
        plt.close(fig2)


if __name__ in "__main__":

    SAVE = False

    # Fig 2 (new): A & B. IPSCs from SOM to PC and NDNF with / without spillover
    exp104_motifs_SOM_PC(mean_pop=False, w_hetero=True, noise=0.1, save=SAVE)
    exp104_motifs_SOM_NDNF(mean_pop=False, w_hetero=True, noise=0.1, save=SAVE)

    # Fig 3: Layer-specificity of NDNF control (with & without pre inh)
    exp103_layer_specificity(mean_pop=False, w_hetero=True, noise=0.1, pre_inh=True, save=SAVE)
    exp103_layer_specificity(mean_pop=False, w_hetero=True, noise=0.1, pre_inh=False, save=SAVE)

    # Fig 3: total dendritic inhibiion
    exp103b_total_dendritic_inhibition(pre_inh=True, save=SAVE, w_hetero=True, mean_pop=False, noise=0.1)
    exp103b_total_dendritic_inhibition(pre_inh=False, save=SAVE, w_hetero=True, mean_pop=False, noise=0.1)

    # Fig 5B: timescale of inhibition (SOM vs NDNF) 
    # (also plots old panel from Fig 1, TODO: remove)
    exp101_paired_recordings_invitro(mean_pop=False, w_hetero=True, noise=0.1, save=SAVE)

    # old stuff:
    # exp103c_amplifcation_ndnf_inhibition(save=True, w_hetero=True, mean_pop=False, noise=0.1)
    # exp102_preinh_bouton_imaging(save=True)

    plt.show()
 