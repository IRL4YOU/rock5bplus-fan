"""Exercise the controller against temporary sysfs fixtures, never hardware.

Die Zeit wird simuliert: Jeder Regeldurchlauf endet in acht Aufrufen von `sleep 0.25`; danach wird der naechste
Temperaturwert eingespielt. `sleep 1` ist der Anlaufimpuls. Aufgezeichnet wird der PWM-Wert bei jedem sleep.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).with_name('rock5bplus-fan.sh').read_text()
PRELUDE = '''
readlink() { printf '%s/devices/platform/pwm-fan\\n' "$FIXTURE"; }
tick=0; calls=0
sleep() {
  echo "$(cat "$FIXTURE/class/hwmon/hwmon37/pwm1") $1" >> "$FIXTURE/trace"
  [[ -f "$FIXTURE/class/thermal/thermal_zone0/mode" ]] && echo "$(cat "$FIXTURE/class/thermal/thermal_zone0/mode") $1" >> "$FIXTURE/zonetrace"
  if [[ $1 == 0.25 ]]; then
    calls=$((calls + 1))
    if (( calls % 8 == 0 )); then
      tick=$((tick + 1))
      next=$(sed -n "$((tick + 1))p" "$FIXTURE/values")
      if [[ -z $next ]]; then kill -TERM $$; else
        printf '%s\\n' "$next" > "$FIXTURE/class/thermal/thermal_zone17/temp"
      fi
    fi
  fi
}
'''


class FanTests(unittest.TestCase):
    def simulate(self, values, missing_sensor=False, duplicate_fan=False, missing_fan=False, unreadable_sensor=False):
        """Gibt (Rueckgabecode, pwm_je_Durchlauf, Anlaufimpulse, Endwert) zurueck."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hw = root / 'class/hwmon/hwmon37'
            hw.mkdir(parents=True)
            (hw / 'name').write_text('pwmfan\n')
            (hw / 'pwm1').write_text('77\n')
            (hw / 'device').symlink_to(root / 'devices/platform/pwm-fan')
            if missing_fan:
                (hw / 'name').write_text('unrelated\n')
            if duplicate_fan:
                other = hw.parent / 'hwmon42'
                other.mkdir()
                (other / 'name').write_text('pwmfan\n')
                (other / 'pwm1').write_text('88\n')
                (other / 'device').symlink_to(root / 'devices/platform/pwm-fan')
            zone = root / 'class/thermal/thermal_zone0'
            zone.mkdir(parents=True)
            (zone / 'type').write_text('other\n')
            (zone / 'mode').write_text('enabled\n')
            (zone / 'policy').write_text('user_space\n')
            (zone / 'trip_point_0_temp').write_text('60000\n')
            sensor = root / 'class/thermal/thermal_zone17'
            sensor.mkdir(parents=True)
            (sensor / 'type').write_text('other\n' if missing_sensor else 'soc-thermal\n')
            (sensor / 'temp').write_text(values[0] + '\n')
            script = SOURCE.replace('/sys/', tmp + '/')
            (root / 'values').write_text('\n'.join(values) + '\n')
            if unreadable_sensor:
                (sensor / 'temp').unlink()
            (root / 'run.sh').write_text(PRELUDE + script)
            result = subprocess.run(['bash', str(root / 'run.sh')], env={**os.environ, 'FIXTURE': tmp},
                                    capture_output=True, text=True, timeout=60)
            lines = (root / 'trace').read_text().splitlines() if (root / 'trace').exists() else []
            ticks = [int(l.split()[0]) for l in lines if l.endswith(' 0.25')][7::8]
            kicks = [i for i, l in enumerate(lines) if l.endswith(' 1')]
            return result.returncode, ticks, len(kicks), (hw / 'pwm1').read_text().strip()

    def zone(self, values):
        """Fuehrt den Regler aus und gibt (Modus je Durchlauf, Zustand der Waermezone am Ende) zurueck."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hw = root / 'class/hwmon/hwmon37'
            hw.mkdir(parents=True)
            (hw / 'name').write_text('pwmfan\n')
            (hw / 'pwm1').write_text('77\n')
            (hw / 'device').symlink_to(root / 'devices/platform/pwm-fan')
            zone = root / 'class/thermal/thermal_zone0'
            zone.mkdir(parents=True)
            for name, text in (('type', 'other'), ('mode', 'enabled'), ('policy', 'user_space'), ('trip_point_0_temp', '60000')):
                (zone / name).write_text(text + '\n')
            sensor = root / 'class/thermal/thermal_zone17'
            sensor.mkdir(parents=True)
            (sensor / 'type').write_text('soc-thermal\n')
            (sensor / 'temp').write_text(values[0] + '\n')
            (root / 'values').write_text('\n'.join(values) + '\n')
            (root / 'run.sh').write_text(PRELUDE + SOURCE.replace('/sys/', tmp + '/'))
            subprocess.run(['bash', str(root / 'run.sh')], env={**os.environ, 'FIXTURE': tmp}, capture_output=True, text=True, timeout=60)
            lines = (root / 'zonetrace').read_text().splitlines()
            modes = [l.split()[0] for l in lines if l.endswith(' 0.25')][7::8]
            final = {n: (zone / n).read_text().strip() for n in ('mode', 'policy', 'trip_point_0_temp')}
            return modes, final

    def test_thermal_zone_is_off_while_running_and_restored_on_exit(self):
        modes, final = self.zone(['50000'] * 4)
        self.assertEqual(set(modes), {'disabled'})
        self.assertEqual(final, {'mode': 'enabled', 'policy': 'step_wise', 'trip_point_0_temp': '84000'})

    def test_thermal_zone_comes_back_as_safety_at_80_degrees_with_hysteresis(self):
        modes, _ = self.zone(['70000', '81000', '78000', '75000', '70000'])
        self.assertEqual(modes[:5], ['disabled', 'enabled', 'enabled', 'disabled', 'disabled'])

    @staticmethod
    def want(temp_mc):
        x = min(max(temp_mc, 45000), 70000)
        return 50 + (x - 45000) * 205 // 25000

    def test_steady_temperatures_settle_on_the_curve(self):
        for temp in (45000, 50000, 57500, 62000, 67999):
            with self.subTest(temp=temp):
                code, ticks, _, final = self.simulate([str(temp)] * 120)
                self.assertEqual(code, 0)
                self.assertEqual(ticks[-1], self.want(temp))
                self.assertEqual(final, '255')          # beim Beenden volle Leistung

    def test_full_power_from_68_degrees(self):
        code, ticks, _, _ = self.simulate(['70000'] * 5)
        self.assertEqual((code, ticks[-1]), (0, 255))

    def test_emergency_at_68_degrees(self):
        code, ticks, _, _ = self.simulate(['46000'] * 60 + ['68000'] + ['46000'] * 3)
        self.assertEqual(code, 0)
        self.assertEqual(ticks[60], 255)               # sofort, ohne Rampe

    def test_no_stop_between_42_and_45_degrees_once_running(self):
        code, ticks, _, _ = self.simulate(['50000'] * 40 + ['43000'] * 150)
        self.assertEqual(code, 0)
        self.assertEqual(min(ticks), 50)               # laeuft leise weiter, geht nicht aus

    def test_switches_off_below_42_and_stays_off_until_45(self):
        code, ticks, kicks, _ = self.simulate(['40000'] * 100 + ['44000'] * 40)
        self.assertEqual(code, 0)
        self.assertEqual(ticks[-1], 0)                 # bei 44 Grad bleibt er aus (kein Pendeln)
        self.assertEqual(ticks.count(0) > 0, True)

    def test_switches_on_with_start_impulse(self):
        code, ticks, kicks, _ = self.simulate(['40000'] * 100 + ['52000'] * 80)
        self.assertEqual(code, 0)
        self.assertEqual(kicks, 2)                     # Start + Wiedereinschalten
        self.assertGreater(ticks[-1], 50)

    def test_changes_are_gradual(self):
        code, ticks, _, _ = self.simulate(['46000'] * 60 + ['58000'] * 30 + ['46000'] * 60)
        self.assertEqual(code, 0)
        for a, b in zip(ticks, ticks[1:]):
            if b > a:
                self.assertLessEqual(b - a, 10)        # hoch hoechstens 10 je Durchlauf
            else:
                self.assertLessEqual(a - b, 3)         # runter hoechstens 3 je Durchlauf

    def test_single_spike_is_smoothed(self):
        code, ticks, _, _ = self.simulate(['46000'] * 60 + ['60000'] + ['46000'] * 5)
        self.assertEqual(code, 0)
        self.assertLessEqual(ticks[61] - ticks[60], 10)

    def test_invalid_sensor(self):
        for value in ['0', '-1', '150000', 'error', '']:
            with self.subTest(value=value):
                code, _, _, final = self.simulate([value])
                self.assertNotEqual(code, 0)
                self.assertEqual(final, '255')

    def test_missing_sensor(self):
        code, _, _, final = self.simulate(['50000'], missing_sensor=True)
        self.assertNotEqual(code, 0)
        self.assertEqual(final, '255')

    def test_sensor_read_failure(self):
        code, _, _, final = self.simulate(['50000'], unreadable_sensor=True)
        self.assertNotEqual(code, 0)
        self.assertEqual(final, '255')

    def test_ambiguous_fan_no_write(self):
        code, ticks, _, final = self.simulate(['50000'], duplicate_fan=True)
        self.assertNotEqual(code, 0)
        self.assertEqual((ticks, final), ([], '77'))

    def test_missing_fan_no_write(self):
        code, ticks, _, final = self.simulate(['50000'], missing_fan=True)
        self.assertNotEqual(code, 0)
        self.assertEqual((ticks, final), ([], '77'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
