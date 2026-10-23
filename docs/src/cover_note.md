**DRAFT FOR LUKE TO EDIT. Do not send as is. Fill in the bracketed parts; nothing is sent by Claude.**

Hi [name],

Following our conversation at [where you met], I built the project I mentioned: a drone camera pipeline that detects and tracks people and vehicles, estimates each one's distance with an error bar, and runs on a laptop CPU.

The part I am most pleased with: on synthetic flights with exact ground truth, estimating the ground from the drone's own motion cut the median distance error to {{RESULT:headline.json#midair_test.terrain_median|.1%}}, against {{RESULT:headline.json#midair_test.flat_alt_median|.0%}} for a flat ground plane with an altimeter. Next, I would test it with a calibrated camera and recorded gimbal angles.

Code and results: [repository link]. Two-minute video: [video link].

Best wishes,
Luke
