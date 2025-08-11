# this script will be to look up the frequency ranges
# of the UHF TV channels from https://en.wikipedia.org/wiki/Pan-American_television_frequencies

import matplotlib.pyplot as plt

channel_dict = {
				'15':{'lower':476, 'upper':482},
				'16':{'lower':482, 'upper':488},
				'17':{'lower':488, 'upper':494},
				'18':{'lower':494, 'upper':500},
				'19':{'lower':500, 'upper':506},
				'20':{'lower':506, 'upper':512},
				'21':{'lower':512, 'upper':518},
				'22':{'lower':518, 'upper':524},
				'23':{'lower':524, 'upper':530},
				'24':{'lower':530, 'upper':536},
				'25':{'lower':536, 'upper':542},
				'26':{'lower':542, 'upper':548},
				'27':{'lower':548, 'upper':554},
				'28':{'lower':554, 'upper':560},
				'29':{'lower':560, 'upper':566},
				'30':{'lower':566, 'upper':572},
				'31':{'lower':572, 'upper':578},
				'32':{'lower':578, 'upper':584},
				'33':{'lower':584, 'upper':590},
				'34':{'lower':590, 'upper':596},
				'35':{'lower':596, 'upper':602},
				'36':{'lower':602, 'upper':608},
				'37':{'lower':608, 'upper':614},
				'38':{'lower':614, 'upper':620},
				'39':{'lower':620, 'upper':626},
				'40':{'lower':626, 'upper':632},
				'41':{'lower':632, 'upper':638},
				'42':{'lower':638, 'upper':644},
				'43':{'lower':644, 'upper':650},
				'44':{'lower':650, 'upper':656},
				'45':{'lower':656, 'upper':662},
				'46':{'lower':662, 'upper':668},
				'47':{'lower':668, 'upper':674},
				'48':{'lower':674, 'upper':680},
				'49':{'lower':680, 'upper':686},
				'50':{'lower':686, 'upper':692},
				'51':{'lower':692, 'upper':698},
				'52':{'lower':698, 'upper':704},
				'53':{'lower':704, 'upper':710},
				'54':{'lower':710, 'upper':716},
				'55':{'lower':716, 'upper':722},
				'56':{'lower':722, 'upper':728},
				'57':{'lower':728, 'upper':734},
				'58':{'lower':734, 'upper':740},
				'59':{'lower':740, 'upper':746},
				'60':{'lower':746, 'upper':752},
				'61':{'lower':752, 'upper':758},
				'62':{'lower':758, 'upper':764},
				'63':{'lower':764, 'upper':770},
				'64':{'lower':770, 'upper':776},
				'65':{'lower':776, 'upper':782},
				'66':{'lower':782, 'upper':788},
				'67':{'lower':788, 'upper':794},
				'68':{'lower':794, 'upper':800},
				'69':{'lower':800, 'upper':806},
				'70':{'lower':806, 'upper':812},
				'71':{'lower':812, 'upper':818},
				'72':{'lower':818, 'upper':824},
				'73':{'lower':824, 'upper':830},
				'74':{'lower':830, 'upper':836},
				'75':{'lower':836, 'upper':842},
				'76':{'lower':842, 'upper':848},
				'77':{'lower':848, 'upper':854},
				'78':{'lower':854, 'upper':860},
				'79':{'lower':860, 'upper':866},
				'80':{'lower':866, 'upper':872},
				'81':{'lower':872, 'upper':878},
				'82':{'lower':878, 'upper':884},
				'83':{'lower':884, 'upper':890},
}


def channel_lookup(freq, unit="MHz"):
    """
    This function will be able to look up the TV channel that covers
    a given frequency
    """
    if unit == "MHz":
        freq = freq
    elif unit == "GHz":
        freq = freq * 1e3
    elif unit == 'Hz':
        freq = freq / 1e6
    else:
        raise "error: invalid units. Please use either Hz, MHz, or GHz" 
    
    channels = list(channel_dict.keys())
    if freq < channel_dict[channels[0]]["lower"] or freq > channel_dict[channels[-1]]["upper"]:
        raise Exception("frequency outside of channel range")
    for chan in channels:
        if freq > channel_dict[chan]["lower"] and freq < channel_dict[chan]["upper"]:
            return chan
    raise Exception("frequency is on boundary of channels")

def plot_channel(ax, channel_number, color="tab:orange", opacity=0.25):
    """
    This function will overlay a shaded region on an existing
    plot and annotate it with the channel number 
    """
    ax.axvspan(channel_dict[channel_number]["lower"], 
                channel_dict[channel_number]["upper"], 
                alpha=opacity, 
                color=color, 
                label=f"TV channel {channel_number}")
