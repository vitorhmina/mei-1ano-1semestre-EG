program HypertrophyBlock {
    const base : float = 80.0;
    const target_rpe : float = 8.0;

    exercise BarbellSquat { category: "lower", equipment: "barbell" }
    exercise PullUp       { category: "upper", equipment: "bodyweight" }

    routine StrengthPhase {
        week 1 {
            session "Monday" {
                var w : float = base * 0.9 + 400;
                do BarbellSquat sets 4 reps 8 load base rpe target_rpe;
                rest 120;
                if (last_rpe > 9.0) {
                    w = w * 0.9;
                } else {
                    w = w + 2.5;
                }
            }
            session "Wednesday" {
                circuit rounds 3 {
                    do PullUp sets 1 reps 10;
                    rest 60;
                }
            }
        }
        week 2 {
            session "Monday" {
                repeat 2 times {
                    do BarbellSquat sets 3 reps 5 load 85.0 rpe 8;
                }
            }
        }
    }
}
