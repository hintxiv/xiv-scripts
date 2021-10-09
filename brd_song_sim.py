from dataclasses import dataclass
import logging
from math import floor
from typing import Dict, Tuple

import numpy as np
import pandas as pd


log = logging.getLogger()
#logging.basicConfig(level=logging.DEBUG)

# region Parameters
POTENCY = {
    'bl': 120,
    'pp1': 100,
    'pp2': 220,
    'pp3': 360,
    'ea': 180, # unknown but close enough to pp3's scaling?
}

MAX_BL_STACKS = 2
INITIAL_BL_STACKS = 0
MAX_PP_STACKS = 3
SPEND_PP_AT = 3
DOTS_UP = 2
GCD_MS = 2460
SONG_DURATION_MS = 45000
# endregion

# region Openers
# Top-level keys: GCD # in the opener
# Secondary keys: Weave slot (either 1st or 2nd)
Opener = Dict[int, Dict[int, str]]

# Totally legit opener :)
GET_STUFF_ON_CD = {
    1: {
        2: 'Raging Strikes',
    },
    2: {
        1: 'Song',
        2: 'Battle Voice',
    },
    3: {
        1: 'Radiant Finale',
    },
    5: {
        1: 'Sidewinder',
        2: 'Barrage',
    },
}

EMPTY_OPENER = {
    1: { 
        1: 'Song',
    }
}
# endregion

# region Logic
@dataclass
class State:
    """Keeps track of some useful data while simming."""
    tick_offset: int = np.random.randint(0, 3000)
    total_potency: int = 0
    time: int = 0
    bl_stacks: int = INITIAL_BL_STACKS
    bl_cd: int = 15000
    bls_used: int = 0
    ea_cd: int = 0
    eas_used: int = 0
    song_began: bool = False
    song_ends_at: int | None = None

    @property
    def time_to_tick(self) -> int:
        """How much time (ms) is left until the next DoT tick."""
        return 3000 - ((self.time - self.tick_offset) % 3000)
    
    @property
    def time_to_weave(self) -> int:
        """How much time (ms) is left until the next weave slot."""
        if self.recast < 750:
            # Next weave is weave 1
            return 750 - self.recast
        elif self.recast < 1500:
            # Next weave is weave 2
            return 1500 - self.recast
        else:
            # Wrap around to weave 1 of the next GCD
            return 750 + (GCD_MS - self.recast)

    @property 
    def recast(self) -> int:
        return self.time % GCD_MS

    @property
    def can_weave(self) -> bool:
        """Returns True if we're at a weave slot."""
        if self.recast == 750 or self.recast == 1500:
            return True

        return False

    @property
    def opener_position(self) -> Tuple[int, int]:
        """Returns the GCD # and weave slot # we're currently at in the opener."""
        gcd = 1 + floor(self.time / GCD_MS)
        weave = 1 if self.recast == 750 else 2

        return gcd, weave

    def on_tick() -> None:
        """Song-specific logic for what happens to the state on DoT tick."""
        raise NotImplementedError

    def update(self) -> None:
        """Move forward in time to the next event."""
        time_elapsed = min(self.time_to_tick, self.time_to_weave)
        self.time += time_elapsed

        # Handle DoTs
        if self.song_began and self.time % 3000 == self.tick_offset:
            for _ in range(DOTS_UP):
                self.on_tick()

        # Natural BL regeneration
        if self.bl_stacks < MAX_BL_STACKS:
            if self.bl_cd - time_elapsed <= 0:
                self.bl_stacks += 1

                # If we're still not at max stacks, lower the CD
                if self.bl_stacks < MAX_BL_STACKS:
                    self.bl_cd = (self.bl_cd - time_elapsed) % 15000
                else:
                    self.bl_cd = 15000            
            else:
                self.bl_cd -= time_elapsed

        # EA regeneration
        if self.ea_cd > 0:
            self.ea_cd = max(0, self.ea_cd - time_elapsed)

    def weave_bl(self) -> None:
        if self.bl_stacks == 0:
            raise ValueError('Tried to use BL with no BL stacks.')     

        if self.bl_stacks == MAX_BL_STACKS:
            # Start a new CD
            self.bl_cd = 15000

        self.total_potency += POTENCY['bl']        
        self.bls_used += 1
        self.bl_stacks -= 1

    def weave_ea(self) -> None:
        if self.ea_cd > 0:
            raise ValueError('Tried to use EA while it was on cooldown.')

        self.total_potency += POTENCY['ea']
        self.eas_used += 1
        self.ea_cd = 15000

@dataclass
class WMState(State):
    pp_stacks: int = 0
    pp3s_used: int = 0
    pp2s_used: int = 0
    pp1s_used: int = 0

    @property
    def average_pp_potency(self) -> float:
        total = self.pp3s_used + self.pp2s_used + self.pp1s_used
        return (self.pp3s_used / total / 3) * POTENCY['pp3'] + \
                (self.pp2s_used / total / 2) * POTENCY['pp2'] + \
                (self.pp1s_used / total) * POTENCY['pp1']

    def on_tick(self) -> None:
        if np.random.uniform() < 0.4:
            # Proc, add a PP stack if we can
            if self.pp_stacks < MAX_PP_STACKS:
                self.pp_stacks += 1

    def weave_pp(self) -> None:
        if self.pp_stacks == 3:
            self.total_potency += POTENCY['pp3']
            self.pp3s_used += 3
        elif self.pp_stacks == 2:
            self.total_potency += POTENCY['pp2']
            self.pp2s_used += 2
        elif self.pp_stacks == 1:
            self.total_potency += POTENCY['pp1']
            self.pp2s_used += 1
        else:
            raise ValueError('Tried to use PP with no PP stacks.')
        
        self.pp_stacks = 0

    def weave_ea(self) -> None:
        super().weave_ea()
        if self.pp_stacks < MAX_PP_STACKS:
            self.pp_stacks += 1

@dataclass
class MBState(State):
    def on_tick(self):
        if np.random.uniform() < 0.4:
            # Proc, add a BL if we can
            if self.bl_stacks < MAX_BL_STACKS:
                self.bl_stacks += 1

        if self.bl_stacks == MAX_BL_STACKS:
            self.bl_cd = 15000

    def weave_ea(self) -> None:
        super().weave_ea()
        if self.bl_stacks < MAX_BL_STACKS:
            self.bl_stacks += 1

@dataclass
class WeaveStrategy:
    """Given a state, executes an oGCD according to the opener and song logic specified."""
    name: str
    opener: Opener

    def __init__(self, opener: Opener) -> None:
        self.opener = opener

    def time_to_free_weave(self, state: State) -> int:
        """Gives the time until the next EMPTY weave slot."""
        gcd, weave = state.opener_position
        free_weave_at = None

        while not free_weave_at:
            # Move to the next weave slot
            if weave == 1:
                weave += 1
            else:
                gcd += 1
                weave = 1

            # Check if it's in the opener
            if gcd not in self.opener or weave not in self.opener[gcd]:
                free_weave_at = (gcd - 1) * GCD_MS + weave * 750

        return free_weave_at - state.time

    def execute_weave(self, state: State) -> str | None:
        """Chooses which oGCD to weave, updates state, and returns the action's name."""
        weave = None

        # If we're supposed to use an oGCD as part of the opener, do that first
        weave = self.opener_logic(state)

        if weave is None:
            # Otherwise, rely on the song logic to choose an oGCD
            weave = self.song_logic(state)

        log.debug(f'[{state.time / 1000:.2f}] Used {weave}')

        return weave

    def opener_logic(self, state: State) -> str | None:
        gcd, weave = state.opener_position

        if gcd in self.opener:
            if weave in self.opener[gcd]:
                # There's something to weave here from the opener
                action_name = self.opener[gcd][weave]
                return action_name

        return None

    def song_logic(self, state: State) -> str | None:
        raise NotImplementedError

class PP3Strategy(WeaveStrategy):
    name = 'PP3'

    def song_logic(self, state: WMState) -> str | None:
        if state.song_began:
            # Highest priority: dump stacks at the end of the song
            if state.pp_stacks > 0 and self.time_to_free_weave(state) > state.song_ends_at - state.time:
                state.weave_pp()
                return 'Pitch perfect (dump)'

            # Second priority: spend PP3
            if state.pp_stacks == MAX_PP_STACKS:
                state.weave_pp()
                return 'Pitch Perfect'

            if state.ea_cd == 0:
                # Third priority: EA if we're at one or fewer stacks
                if state.pp_stacks <= 1:
                    state.weave_ea()
                    return 'Empyreal Arrow'

                # Fourth priority: EA if we're at 2 stacks and our next 
                #  weave happens before the next DoT tick
                if state.pp_stacks == 2 and self.time_to_free_weave(state) < state.time_to_tick:
                    state.weave_ea()
                    return 'Empyreal Arrow'

        # Final priority: spend natural BL
        if state.bl_stacks > 0:
            state.weave_bl()
            return 'Bloodletter'

        # Nothing to do
        return None

class PP2Strategy(WeaveStrategy):
    name = 'PP2'

    def song_logic(self, state: WMState) -> str | None:
        if state.song_began:
            # Highest priority: dump stacks at the end of the song
            if state.pp_stacks > 0 and self.time_to_free_weave(state) > state.song_ends_at - state.time:
                state.weave_pp()
                return 'Pitch perfect (dump)'

            # Second priority: PP3
            if state.pp_stacks == MAX_PP_STACKS:
                state.weave_pp()
                return 'Pitch Perfect'

            if state.ea_cd == 0:
                # Third priority: EA if we're at one or fewer stacks
                if state.pp_stacks <= 1:
                    state.weave_ea()
                    return 'Empyreal Arrow'

                # Fourth priority: EA if we're at 2 stacks and our next 
                #  weave happens before the next DoT tick
                if state.pp_stacks == 2 and self.time_to_free_weave(state) < state.time_to_tick:
                    state.weave_ea()
                    return 'Empyreal Arrow'

            # Fifth priority: PP2 
            if state.pp_stacks == 2:
                state.weave_pp()
                return 'Pitch Perfect'

        # Final priority: spend natural BL
        if state.bl_stacks > 0:
            state.weave_bl()
            return 'Bloodletter'

        # Nothing to do
        return None

class MBStrategy(WeaveStrategy):
    name = 'Greedy EA MB'

    def song_logic(self, state: MBState) -> str | None:
        if state.song_began and state.ea_cd == 0:
            # Highest priority: EA if we're at 0 stacks
            if state.bl_stacks == 0:
                state.weave_ea()
                return 'Empyreal Arrow'

            # Second priority: EA if we're at 1 stack and our next 
            #  weave happens before the next DoT tick
            if state.bl_stacks == 1 and self.time_to_free_weave(state) < state.time_to_tick:
                state.weave_ea()
                return 'Empyreal Arrow'

        # Third priority: BL
        if state.bl_stacks > 0:
            state.weave_bl()
            return 'Bloodletter'

class SafeMBStrategy(WeaveStrategy):
    name = 'Safe EA MB'

    def song_logic(self, state: MBState) -> str | None:
        ttw = self.time_to_free_weave(state)
        ttt = state.time_to_tick

        if state.song_began and state.ea_cd == 0:
            # Highest priority: EA if we're at 0 stacks and our next
            #  weave happens before the next DoT tick and before a natural BL
            if state.bl_stacks == 0 and ttw < ttt and ttw < state.bl_cd:
                state.weave_ea()
                return 'Empyreal Arrow'

        # Second priority: BL
        if state.bl_stacks > 0:
            state.weave_bl()
            return 'Bloodletter'

class Song:
    name: str
    strategy: WeaveStrategy
    stateCtor: State

    def __init__(self, opener: Opener, strategy: WeaveStrategy):
        self.strategy = strategy(opener)

    def sim(self) -> State:
        """Returns the total potency from one 'run' of the song."""
        state = self.stateCtor()

        while (not state.song_began) or state.time < state.song_ends_at:
            if state.can_weave:
                weave = self.strategy.execute_weave(state)

                if weave == 'Song':
                    # Song was used in the opener
                    state.song_began = True
                    state.song_ends_at = state.time + SONG_DURATION_MS

            state.update()

        return state


class Minuet(Song):
    name = "wm"
    stateCtor = WMState

class Ballad(Song):
    name = "mb"
    stateCtor = MBState
# endregion

# region Simulate
def simulate(song: Song, iters = 1000) -> pd.DataFrame:
    data = pd.DataFrame(columns=['strategy', 'iter', 'avg potency', 'pp3s', 'pp2s', 'pp1s', 'bls', 'eas', 'avg pp'])

    for i in range(iters):
        state = song.sim()
        if song.name == 'wm':
            data.loc[i] = [song.strategy.name] + [i] + [(state.total_potency / state.time) * 1000] + [state.pp3s_used] + \
                        [state.pp2s_used] + [state.pp1s_used] + [state.bls_used] + [state.eas_used] + \
                        [state.average_pp_potency]
        
        elif song.name == 'mb':
            data.loc[i] = [song.strategy.name] + [i] + [(state.total_potency / state.time) * 1000] + [0] + [0] + [0] + \
                        [state.bls_used] + [state.eas_used] + [0]

    return data
# endregion

if __name__ == "__main__":
    # Use this for "vacuum" sims
    opener = EMPTY_OPENER 
    # Use this for "opener-like" sims with lots of priority weaves
    # opener = GET_STUFF_ON_CD

    pp3_data = simulate(Minuet(opener, PP3Strategy))
    pp2_data = simulate(Minuet(opener, PP2Strategy))
    mb_data = simulate(Ballad(opener, MBStrategy))
    mb_safe_data = simulate(Ballad(opener, SafeMBStrategy))

    # Output some numerical summaries
    print('No opener, 0 initial BL stacks\n\n')
    print('WM: PP3 Strategy')
    print(f"Avg. PP stacks used: {pp3_data['pp3s'].mean() + pp3_data['pp2s'].mean() + pp3_data['pp1s'].mean()}, Avg. potency per stack: {pp3_data['avg pp'].mean()}, Avg. EA uses: {pp3_data['eas'].mean()}")
    print(pp3_data.describe())
    print('--------------------------------')
    print('WM: PP2 Strategy')
    print(f"Avg. PP stacks used: {pp2_data['pp3s'].mean() + pp2_data['pp2s'].mean() + pp2_data['pp1s'].mean()}, Avg. potency per stack: {pp2_data['avg pp'].mean()}, Avg. EA uses: {pp2_data['eas'].mean()}")
    print(pp2_data.describe())
    print('--------------------------------')
    print('MB: Greedy EA Strategy')
    print(f"Avg. BL uses: {mb_data['bls'].mean()}, Avg. EA uses: {mb_data['eas'].mean()}")
    print(mb_data.describe())
    print('--------------------------------')
    print('MB: Safe EA Strategy')
    print(f"Avg. BL uses: {mb_safe_data['bls'].mean()}, Avg. EA uses: {mb_safe_data['eas'].mean()}")
    print(mb_safe_data.describe())
