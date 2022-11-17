"""
Experiments on the network model.
"""

import numpy as np
import matplotlib.pyplot as plt
from model_base import get_default_params, NetworkModel
plt.style.use('pretty')

# ToDo: make experiments classes?

# colours
cPC = '#B83D49'
cPV = '#345377'
cSOM = '#5282BA'
cNDNF = '#E18E69'
cVIP = '#D1BECF'
cpi = '#A7C274'


def ex_activation_inactivation():
    """
    Experiment: activate and inactive different cell types and check effect on all other cells. Plots big fig array of
    results. Mostly for rough inspection of the model
    """

    # simulation parameters
    dur = 700
    dt = 1
    nt = int(dur/dt)

    # activation/inactivation parameters
    ts, te = 300, 450  # start and end point of activation
    I_activate = 1  # -1 for inactivation

    # get default parameters
    N_cells, w_mean, conn_prob, bg_inputs, taus = get_default_params()
    wED = 1

    # parameters can be adapted: e.g.
    # w_mean['PN'] = 1

    # initialise model
    model = NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=wED, flag_SOM_ad=False,
                         flag_w_hetero=False, flag_pre_inh=False, flag_with_VIP=True, flag_with_NDNF=False)

    # print stuff about weights (derived from math, indicate effect of SOM input on PC and PV)
    # ToDo: remove in the future
    gamma = w_mean['EP']*w_mean['PS'] - wED*w_mean['DS']
    print(w_mean['EP']*w_mean['PS'], wED*w_mean['DS'], 'gamma=', gamma)
    # print(1+w_mean['EP']*w_mean['PE'], (w_mean['EP']*w_mean['PS']-wED*w_mean['DS'])*w_mean['SE'])
    print(w_mean['PE'], w_mean['PS']*w_mean['SE'])
    print((w_mean['PE']-w_mean['PS']*w_mean['SE'])*gamma/(1+w_mean['EP']*w_mean['PE']-gamma), w_mean['PS'] )

    # create empty figure
    fig1, ax1 = plt.subplots(6, 6, figsize=(6, 5), dpi=150, sharex=True, sharey='row', gridspec_kw={'right': 0.95})

    # Activation/ Inactivation of different cell types
    for i, cell in enumerate(['E', 'D', 'S', 'N', 'P', 'V']):

        # create FF inputs (i.e. stimulation)
        xFF = get_null_ff_input_arrays(nt, N_cells)
        xFF[cell][ts:te, :] = I_activate  # N_cells[cell]//2

        # run network
        t, rE, rD, rS, rN, rP, rV, p, other = model.run(dur, xFF, dt=dt, init_noise=0)

        # plot
        ax1[0, i].plot(t, rE, c='C3', alpha=0.5)
        ax1[1, i].plot(t, rD, c='darkred', alpha=0.5)
        ax1[2, i].plot(t, rS, c='C0', alpha=0.5)
        ax1[3, i].plot(t, rN, c='C1', alpha=0.5)
        ax1[4, i].plot(t, rP, c='darkblue', alpha=0.5)
        ax1[5, i].plot(t, rV, c='C4', alpha=0.5)
        ax1[0, i].set(title='act. '+cell)
        ax1[-1, i].set(xlabel='time (ms)')  #, ylim=[0, 1])

    # add labels for rows
    for j, name in enumerate(['PC', 'dend', 'SOM', 'NDNF', 'PV', 'VIP']):
        ax1[j, 0].set(ylabel=name, ylim=[0, 2.5])


def fig1_paired_recordings_invitro(dur=300, dt=1):
    """
    Run experiment of paired "in vitro" recordings and plot.
    :param dur:  length of experiment
    :param dt:   time step
    """

    # simulation paramters
    nt = int(dur / dt)
    t = np.arange(0, dur, dt)
    t0 = 50

    # create figure
    fig, ax = plt.subplots(2, 2, figsize=(3, 1.7), dpi=400, sharex=True, sharey='row',
                           gridspec_kw={'right': 0.95, 'bottom': 0.21, 'left': 0.15})

    # get default parameters
    N_cells, w_mean, conn_prob, bg_inputs, taus = get_default_params()

    # stimulate SOM and NDNF, respectively
    for i, cell in enumerate(['S', 'N']):
        # array of FF input
        xFF = get_null_ff_input_arrays(nt, N_cells)
        xFF[cell][:, :] = 2 * np.tile(np.exp(-(t - t0) / 50) * np.heaviside(t - t0, 1), (N_cells[cell], 1)).T
        # create model and run
        model = NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_SOM_ad=False,
                             flag_w_hetero=False, flag_pre_inh=False, flag_with_VIP=False, flag_with_NDNF=True)
        t, rE, rD, rS, rN, rP, rV, p, other = model.run(dur, xFF, dt=dt, init_noise=0, monitor_currents=True,
                                                        rE0=0, rD0=0, rN0=0, rS0=0, rP0=0)

        # plotting and labels
        ax[0, i].plot(t[1:], other['curr_rS'], c=cSOM)
        ax[1, i].plot(t[1:], other['curr_rN'], c=cNDNF)
        ax[1, i].set(xlabel='time (ms)', ylim=[-0.1, 3])
    ax[0, 0].set(ylim=[-2, 2], ylabel='curr. (au)')
    ax[1, 0].set(ylim=[-2, 2], ylabel='curr. (au)')


def fig1_activation(I_activate=1, dur=1000, ts=400, te=600, dt=1):
    """
    Hacky function to test activation of SOM/NDNF/VIP in networks with NDNFs and VIPs, respectively. Plots first draft
    for different panels in Figure 1.

    :param I_activate:  activation input
    :param dur:         duration of experiment (in ms)
    :param ts:          start time of stimulation
    :param te:          end time of stimulation
    :param dt:          time step
    """

    nt = int(dur/dt)

    # i) default, with NDNF
    fig1, ax1 = plt.subplots(4, 2, figsize=(2, 2), dpi=300, sharex=True, sharey='row', gridspec_kw={'right': 0.95})
    N_cells, w_mean, conn_prob, bg_inputs, taus = get_default_params()
    for i, cell in enumerate(['S', 'N']):
        xFF = get_null_ff_input_arrays(nt, N_cells)
        xFF[cell][ts:te, :] = I_activate
        model = NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_SOM_ad=False,
                             flag_w_hetero=False, flag_pre_inh=False, flag_with_VIP=False, flag_with_NDNF=True)
        t, rE, rD, rS, rN, rP, rV, p, other = model.run(dur, xFF, dt=dt, init_noise=0)
        ax1[0, i].plot(t, rE, c=cPC, alpha=0.5)
        ax1[1, i].plot(t, rP, c=cPV, alpha=0.5)
        ax1[2, i].plot(t, rS, c=cSOM, alpha=0.5)
        ax1[3, i].plot(t, rN, c=cNDNF, alpha=0.5)
        for j in range(4):
            ax1[j, i].axis('off')

    # ii) default, with VIP
    fig2, ax2 = plt.subplots(4, 2, figsize=(2, 2), dpi=300, sharex=True, sharey='row', gridspec_kw={'right': 0.95})
    N_cells, w_mean, conn_prob, bg_inputs, taus = get_default_params()
    for i, cell in enumerate(['S', 'V']):

        xFF = get_null_ff_input_arrays(nt, N_cells)
        xFF[cell][ts:te, :] = I_activate
        model = NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_SOM_ad=False,
                             flag_w_hetero=False, flag_pre_inh=False, flag_with_VIP=True, flag_with_NDNF=False)
        t, rE, rD, rS, rN, rP, rV, p, other = model.run(dur, xFF, dt=dt, init_noise=0)

        ax2[0, i].plot(t, rE, c=cPC, alpha=0.5)
        ax2[1, i].plot(t, rP, c=cPV, alpha=0.5)
        ax2[2, i].plot(t, rS, c=cSOM, alpha=0.5)
        ax2[3, i].plot(t, rV, c=cVIP, alpha=0.5)
        for j in range(4):
            ax2[j, i].axis('off')

    # iii) stim SOM, different settings
    fig2, ax3 = plt.subplots(4, 2, figsize=(2, 2), dpi=300, sharex=True, sharey='row', gridspec_kw={'right': 0.95})
    N_cells, w_mean, conn_prob, bg_inputs, taus = get_default_params()

    # a: disinhibition-dominated
    w_mean = dict(NS=1, DS=0.5, DN=1.5, SE=0.5, NN=0, PS=0.5, PN=0.5, PP=0, PE=0.7, EP=1, DE=0, VS=0, SV=0)
    xFF = get_null_ff_input_arrays(nt, N_cells)
    xFF['S'][ts:te, :] = I_activate
    model = NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_SOM_ad=False,
                         flag_w_hetero=False, flag_pre_inh=False, flag_with_VIP=False, flag_with_NDNF=True)
    t, rE, rD, rS, rN, rP, rV, p, other = model.run(dur, xFF, dt=dt, init_noise=0)
    ax3[0, 0].plot(t, rE, c=cPC, alpha=0.5)
    ax3[1, 0].plot(t, rP, c=cPV, alpha=0.5)
    ax3[2, 0].plot(t, rS, c=cSOM, alpha=0.5)
    ax3[3, 0].plot(t, rN, c=cNDNF, alpha=0.5)

    # b: same but NDNF inactive
    model = NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_SOM_ad=False,
                         flag_w_hetero=False, flag_pre_inh=False, flag_with_VIP=False, flag_with_NDNF=True)
    t, rE, rD, rS, rN, rP, rV, p, other = model.run(dur, xFF, dt=dt, init_noise=0, rN0=0)
    ax3[0, 1].plot(t, rE, c=cPC, alpha=0.5)
    ax3[1, 1].plot(t, rP, c=cPV, alpha=0.5)
    ax3[2, 1].plot(t, rS, c=cSOM, alpha=0.5)
    ax3[3, 1].plot(t, rN, c=cNDNF, alpha=0.5)

    for j in range(4):
        ax3[j, 0].axis('off')
        ax3[j, 1].axis('off')


def fig1_weights_role(I_activate=1, dur=1000, ts=400, te=600, dt=1, save=False, noise=0.0):
    """
    Hacky function to plot effect of different weights on the responses to simulated optogenetic experiments.
    Plots figure panel draft for fig 1.

    :param I_activate:  activation input
    :param dur:         duration of experiment (in ms)
    :param ts:          start time of stimulation
    :param te:          end time of stimulation
    :param dt:          time step
    """

    nt = int(dur / dt)

    # create figure
    dpi = 400 if save else 200
    fig, ax = plt.subplots(1, 2, figsize=(2.8, 1.5), dpi=400, sharex=False, sharey='row',
                           gridspec_kw={'right': 0.95, 'left':0.16, 'bottom':0.25})

    # use paramterisation from disinhibition-dominated regime (overwrite w_mean)
    N_cells, w_mean, conn_prob, bg_inputs, taus = get_default_params()
    w_mean_df = dict(NS=0.9, DS=0.5, DN=1.5, SE=0.5, NN=0.2, PS=0.8, PN=0.5, PP=0.1, PE=1, EP=0.5, DE=0, VS=0, SV=0)
    # w_mean_df = dict(NS=1, DS=0.5, DN=1.5, SE=0.5, NN=0, PS=0.5, PN=0.5, PP=0, PE=0.7, EP=1, DE=0, VS=0, SV=0)
    w_mean = w_mean_df.copy()

    # create input (stimulation of SOMs)
    xFF = get_null_ff_input_arrays(nt, N_cells)
    xFF['S'][ts:te, :] = I_activate

    # vary wPN
    change_rE_wPN = []
    change_rP_wPN = []
    wPN_range = np.arange(0, 2.1, 0.1)
    for wPN in wPN_range:
        w_mean['PN'] = wPN
        model = NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_SOM_ad=False,
                             flag_w_hetero=True, flag_pre_inh=False, flag_with_VIP=False, flag_with_NDNF=True)
        t, rE, rD, rS, rN, rP, rV, p, other = model.run(dur, xFF, dt=dt, init_noise=0, noise=noise)
        change_rE_wPN.append(np.mean(rE[ts:te])/np.mean(rE[:te-ts]))
        change_rP_wPN.append(np.mean(rP[ts:te])/np.mean(rP[:te-ts]))
    ax[0].plot(wPN_range, change_rE_wPN, cPC)
    ax[0].plot(wPN_range, change_rP_wPN, cPV)

    # vary wDN
    w_mean = w_mean_df.copy()
    change_rE_wDN = []
    change_rP_wDN = []
    wDN_range = np.arange(0, 2.1, 0.1)
    for wDN in wDN_range:
        w_mean['DN'] = wDN
        model = NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_SOM_ad=False,
                            flag_w_hetero=False, flag_pre_inh=False, flag_with_VIP=False, flag_with_NDNF=True)
        t, rE, rD, rS, rN, rP, rV, p, other = model.run(dur, xFF, dt=dt, init_noise=0)
        change_rE_wDN.append(np.mean(rE[ts:te])/np.mean(rE[:te-ts]))
        change_rP_wDN.append(np.mean(rP[ts:te])/np.mean(rP[:te-ts]))
    ax[1].plot(wDN_range, change_rE_wDN, cPC)
    ax[1].plot(wDN_range, change_rP_wDN, cPV)

    # pretty up the plot
    ax[0].hlines(1, 0, 2, ls='--', color='silver', lw=1, zorder=-1)
    ax[1].hlines(1, 0, 2, ls='--', color='silver', lw=1, zorder=-1)
    ax[0].set(xlabel='NDNF->PV', ylabel='rate change (rel)', ylim=[0.5, 1.6], yticks=[0.5, 1, 1.5])
    ax[1].set(xlabel='NDNF->dendrite')

    if save:
        plt.savefig('../results/figs/tmp/'+save, dpi=400)


def ex_perturb_circuit(save=False, I_activate=1, dur=1000, ts=400, te=600, dt=1, noise=0.0):
    """
    Experiment: stimulate SOM for the default parameters and the disinhibition-dominated regime
    """

    # number of timesteps
    nt = int(dur/dt)

    # get default parameters and weights for disinhibition-dominated regime
    N_cells, w_mean, conn_prob, bg_inputs, taus = get_default_params()
    w_mean['DS'] = 1.2
    w_mean_disinh = dict(NS=0.9, DS=0.5, DN=1.5, SE=0.5, NN=0.2, PS=0.8, PN=0.5, PP=0.1, PE=1, EP=0.5, DE=0, VS=0, SV=0)

    # create stimulus array
    xFF = get_null_ff_input_arrays(nt, N_cells)
    xFF['S'][ts:te, :] = I_activate

    # set up models
    model = NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=0.7, flag_w_hetero=True, flag_pre_inh=False)
    model_disinh = NetworkModel(N_cells, w_mean_disinh, conn_prob, taus, bg_inputs, wED=0.7, flag_w_hetero=True,
                                flag_pre_inh=False)

    # run and plot for default and disinhibition-dominated model
    dpi = 400 if save else 200
    fig, ax = plt.subplots(4, 2, dpi=dpi, figsize=(1.7, 1.7), sharex=True, gridspec_kw={'top':0.95, 'bottom': 0.05})
    for i, mod in enumerate([model, model_disinh]):
        t, rE, rD, rS, rN, rP, rV, p, other = mod.run(dur, xFF, dt=dt, init_noise=0, noise=noise)

        ax[0, i].plot(t, rN, c=cNDNF, alpha=0.5, lw=0.8)
        ax[1, i].plot(t, rS, c=cSOM, alpha=0.5, lw=0.8)
        ax[2, i].plot(t, rP, c=cPV, alpha=0.5, lw=0.8)
        ax[3, i].plot(t, rE, c=cPC, alpha=0.5, lw=0.8)

        for axx in ax[:, i]:
            axx.set(ylim=[-0.1, 2.3])
            axx.axis('off')

    if save:
        plt.savefig('../results/figs/tmp/'+save, dpi=400)


def ex_bouton_imaging(dur=1000, ts=300, te=400, dt=1, stim_NDNF=2, noise=0.0, flag_w_hetero=False):
    """
    Experiment: Image SOM bouton in response to stimulation of NDNF interneurons.
    - dur: duration of experiment (ms)
    - ts: start of NDNF stimulation
    - te: end of NDNF stimulation
    - dt: integration time step (ms)
    - stim_NDNF: strength of NDNF stimulation
    - noise: level of white noise added to neural activity
    - flag_w_hetero: whether to add heterogeneity to weight matrices
    """

    # define parameter dictionaries
    N_cells, w_mean, conn_prob, bg_inputs, taus = get_default_params()

    # instantiate model
    model = NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_w_hetero=flag_w_hetero,
                         flag_pre_inh=True)

    # simulation paramters
    nt = int(dur/dt)

    # generate inputs
    xFF = get_null_ff_input_arrays(nt, N_cells)
    xFF['N'][ts:te] = stim_NDNF

    # run model
    t, rE, rD, rS, rN, rP, rV, p, other = model.run(dur, xFF, init_noise=0.1, noise=noise, dt=dt, monitor_boutons=True,
                                                    monitor_currents=True, calc_bg_input=True)

    # plotting
    # --------
    # 3 different plots here: an overview plot, bouton imaging + quantification and only bouton imaging
    fig, ax = plt.subplots(6, 1, figsize=(4, 5), dpi=150, sharex=True)
    ax[0].plot(t, rE, c='C3', alpha=0.5)
    ax[1].plot(t, rD, c='k', alpha=0.5)
    ax[2].plot(t, rS, c='C0', alpha=0.5)
    ax[3].plot(t, rN, c='C1', alpha=0.5)
    ax[4].plot(t, rP, c='darkblue', alpha=0.5)
    ax[5].plot(t, p, c='C2', alpha=1)

    # label stuff
    for i, label in enumerate(['PC', 'dend.', 'SOM', 'NDNF', 'PV']):
        ax[i].set(ylabel=label, ylim=[0, 3])
    ax[5].set(ylabel='p', ylim=[0, 1], xlabel='time (ms)')

    fig2, ax2 = plt.subplots(1, 1, figsize=(3, 2), dpi=300, gridspec_kw={'left':0.3, 'right':0.9, 'bottom':0.35})
    boutons = np.array(other['boutons_SOM'])
    boutons_nonzero = boutons[:, np.mean(boutons, axis=0) > 0]
    cm = ax2.pcolormesh(boutons_nonzero.T, cmap='Blues', vmin=0, vmax=0.15)
    plt.colorbar(cm, ticks=[0, 0.1])
    ax2.set(xlabel='time (ms)', ylabel='# bouton', yticks=[0, 400], xticks=[0, 1000])

    boutons_NDNFact = np.mean(boutons_nonzero[ts:te], axis=0)
    boutons_cntrl = np.mean(boutons_nonzero[0:ts], axis=0)

    fig3, ax3 = plt.subplots(1, 1, figsize=(2, 1.5), dpi=300, gridspec_kw={'left': 0.25, 'right':0.9, 'bottom':0.15})
    plot_violin(ax3, 0, boutons_cntrl, color=cSOM)
    plot_violin(ax3, 1, boutons_NDNFact, color='#E9B86F')

    # vl2 = ax3.violinplot(boutons_NDNFact, positions=[1])
    # for pc in vl1['bodies']:
    #     pc.set_facecolor(cSOM)
    #     pc.set_edgecolor(cSOM)
    # for pc in vl2['bodies']:
    #     pc.set_facecolor('#E9B86F')
    #     pc.set_edgecolor('#E9B86F')
    ax3.set(xlim=[-0.5, 1.5], xticks=[0, 1], xticklabels=['ctrl', 'NDNF act.'], ylim=[0, 0.12], yticks=[0, 0.1],
            ylabel='SOM bouton act.')


def ex_layer_specific_inhibition(dur=1000, dt=1, noise=0.0, flag_w_hetero=True, save=False):
    """
    Experiment: Vary input to NDNF interneurons, monitor NDNF- and SOM-mediated dendritic inhibition and their activity.
    - dur: duration of experiment (ms)
    - dt: integration time step (ms)
    - noise: level of white noise added to neural activity
    - flag_w_hetero: whether to add heterogeneity to weight matrices
    - save: if it's a string, name of the saved file, else if False nothing is saved
    """

    # extract number of timesteps
    nt = int(dur / dt)

    # get default parameters
    N_cells, w_mean, conn_prob, bg_inputs, taus = get_default_params()

    # array for varying NDNF input
    ndnf_input = np.arange(-1, 1, 0.05)

    # empty arrays for recording stuff
    rS_inh_record = []
    rN_inh_record = []
    rS_record = []
    rN_record = []

    for i, I_activate in enumerate(ndnf_input):

        # create input (stimulation of NDNF)
        xFF = get_null_ff_input_arrays(nt, N_cells)
        xFF['N'][:, :] = I_activate

        # instantiate and run model
        model = NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=1, flag_w_hetero=flag_w_hetero,
                             flag_pre_inh=True)
        t, rE, rD, rS, rN, rP, rV, p, other = model.run(dur, xFF, dt=dt, init_noise=0, monitor_dend_inh=True,
                                                        noise=noise)

        # save stuff
        rS_record.append(rS[-1])
        rN_record.append(rN[-1])
        rS_inh_record.append(np.mean(np.array(other['dend_inh_SOM'][-1])))
        rN_inh_record.append(np.mean(np.array(other['dend_inh_NDNF'][-1])))

    # plotting
    dpi = 400 if save else 200
    fig, ax = plt.subplots(2, 1, figsize=(2, 2.8), dpi=dpi, gridspec_kw={'left': 0.25, 'bottom': 0.15, 'top': 0.95,
                                                                       'height_ratios': [1, 1]}, sharex=True)
    ax[0].plot(ndnf_input, rS_inh_record, c=cSOM, ls='--')
    ax[0].plot(ndnf_input, rN_inh_record, c=cNDNF, ls='--')
    ax[1].plot(ndnf_input, np.mean(np.array(rS_record), axis=1), c=cSOM)
    ax[1].plot(ndnf_input, np.mean(np.array(rN_record), axis=1), c=cNDNF)

    # labels etc
    ax[0].set(ylabel='dend. inhibition (au)', ylim=[-0.05, 1], yticks=[0, 1])
    ax[1].set(xlabel='input to NDNF (au)', ylabel='neural activity (au)', xlim=[-1, 1], ylim=[-0.1, 2.5],
              yticks=[0, 1, 2])

    # saving
    if save:
        plt.savefig('../results/figs/tmp/'+save, dpi=400)


def ex_switch_activity(noise=0.0, flag_w_hetero=True, save=False):
    """
    Experiment: Switch between NDNDF and SOM-dominated dendritic inhibition. Network is in bistable mututal inhibition
                regime. Activate and inactive NDNF interneurons to create switching.
    - noise: level of white noise added to neural activity
    - flag_w_hetero: whether to add heterogeneity to weight matrices
    - save: if it's a string, name of the saved file, else if False nothing is saved
    """

    # define parameter dictionaries
    N_cells, w_mean, conn_prob, bg_inputs, taus = get_default_params(flag_mean_pop=False)

    # increase SOM to NDNF inhibition to get bistable regime
    w_mean['NS'] = 1.4

    # instantiate model
    model = NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, wED=0.7, flag_w_hetero=flag_w_hetero,
                         flag_pre_inh=True)

    # simulation paramters
    dur = 3000
    dt = 1
    nt = int(dur/dt)

    # generate inputs
    t_act_s, t_act_e = 500, 1000
    t_inact_s, t_inact_e = 2000, 2500
    xFF = get_null_ff_input_arrays(nt, N_cells)
    xFF['N'][t_act_s:t_act_e] = 1.5
    xFF['N'][t_inact_s:t_inact_e] = -1.5

    # run model
    t, rE, rD, rS, rN, rP, rV, p, other = model.run(dur, xFF, dt=dt, p0=0.5, init_noise=0, calc_bg_input=True,
                                                    monitor_dend_inh=True, noise=noise)

    # plotting
    dpi = 400 if save else 200
    fig, ax = plt.subplots(3, 1, figsize=(2, 2.8), dpi=dpi, sharex=True,
                           gridspec_kw={'left': 0.25, 'bottom': 0.15, 'top': 0.95, 'height_ratios': [1, 1, 0.5]})
    ax[1].plot(t/1000, rN, c=cNDNF, alpha=0.5)
    ax[1].plot(t/1000, rS, c=cSOM, alpha=0.5)
    ax[0].plot(t/1000, np.mean(np.array(other['dend_inh_NDNF']), axis=1), c=cNDNF, ls='--')
    ax[0].plot(t/1000, np.mean(np.array(other['dend_inh_SOM']), axis=1), c=cSOM, ls='--')
    ax[2].plot(t/1000, p, c=cpi, alpha=1)

    # labels etc
    ax[0].set(ylabel='dend. inh. (au)', ylim=[-0.1, 1.5], yticks=[0, 1])
    ax[1].set(ylabel='activity (au)', ylim=[-0.1, 3.5], yticks=[0, 2])
    ax[2].set(ylabel='release', ylim=[-0.05, 1.05], yticks=[0, 1], xlabel='time (s)', xticks=[0, 1, 2, 3])

    # saving (optional)
    if save:
        plt.savefig('../results/figs/tmp/'+save, dpi=400)


def plot_gfunc(b=0.5, save=False):
    """
    Plot presynaptic inhibition transfer function.
    - b: strength of presynaptic inhibition
    - save: if it's a string, name of the saved file, else if False nothing is saved

    """

    # get default parameters and instantiate model
    N_cells, w_mean, conn_prob, bg_inputs, taus = get_default_params()
    model = NetworkModel(N_cells, w_mean, conn_prob, taus, bg_inputs, flag_pre_inh=True, b=b)

    # get release probability for range of NDNF activity
    ndnf_act = np.arange(0, 2.5, 0.1)
    p = model.g_func(ndnf_act)

    # plotting
    fig, ax = plt.subplots(1, 1, figsize=(2, 1.5), dpi=400, gridspec_kw={'left': 0.25, 'bottom':0.25})
    ax.plot(ndnf_act, p, c=cpi)
    ax.set(xlabel='NDNF activity (au)', ylabel='release factor', xlim=[0, 2.5], ylim=[-0.05, 1], xticks=[0, 1, 2],
           yticks=[0, 1])

    # saving (optional)
    if save:
        plt.savefig('../results/figs/tmp/'+save, dpi=400)


def plot_violin(ax, pos, data, color=None, showmeans=True):
    """
    Makes violin of data at x position pos in axis object ax.
    - data is an array of values
    - pos is a scalar
    - ax is an axis object

    Kwargs: color (if None default mpl is used) and whether to plot the mean
    """

    parts = ax.violinplot(data, positions=[pos], showmeans=showmeans, widths=0.6)
    if color:
        for pc in parts['bodies']:
            pc.set_color(color)
        for partname in ('cbars', 'cmins', 'cmaxes', 'cmeans'):
            vp = parts[partname]
            vp.set_edgecolor(color)
            vp.set_linewidth(1)


def get_null_ff_input_arrays(nt, N_cells):
    """
    Generate empty arrays for feedforward input.
    :param nt:      Number of timesteps
    :param Ncells:  Dictionary of cell numbers (soma E, dendrite E, SOMs S, NDNFs N, PVs P)
    :return:        Dictionary with an empty array of size nt x #cell for each neuron type
    """

    xFF_null = dict()
    for key in N_cells.keys():
        xFF_null[key] = np.zeros((nt, N_cells[key]))

    return xFF_null


if __name__ in "__main__":

    # run different experiments; comment in or out to run only some of them

    # ex_activation_inactivation()
    # fig1_paired_recordings_invitro()
    # fig1_activation()
    # fig1_weights_role()
    # ex_bouton_imaging()

    # generating figures for cosyne abstract submission
    noise = 0.15
    ex_layer_specific_inhibition(save='fig2c.pdf', noise=noise)
    ex_switch_activity(save='fig2d.pdf', noise=noise)
    # plot_gfunc(save='fig2b.pdf')
    ex_perturb_circuit(save='fig1b.pdf', noise=noise)
    fig1_weights_role(save='fig1c.pdf', noise=noise)
    plt.show()