program UpperLower {
    const squat_1rm : float = 140.0;
    const bench_1rm : float = 100.0;

    exercise Squat            { category: "lower", equipment: "barbell" }
    exercise RomanianDeadlift { category: "lower", equipment: "barbell" }
    exercise BenchPress       { category: "upper", equipment: "barbell" }
    exercise Row              { category: "upper", equipment: "barbell" }
    exercise PullUp           { category: "upper", equipment: "bodyweight" }

    routine Strength {
        week 1 {
            monday {
                session "Lower" {
                    var back_off : float = squat_1rm * 0.65;
                    do Squat sets 4 reps 5 load squat_1rm * 0.75 rpe 7;
                    rest 180;
                    if (last_rpe > 9.0) {                  // autorregulação
                        back_off = back_off - 5.0;
                    } else {
                        back_off = back_off + 2.5;
                    }
                    do Squat sets 2 reps 8 load back_off rpe 7;
                    rest 120;
                    do RomanianDeadlift sets 3 reps 8 load 90.0 rpe 7;
                }
            }
            thursday {
                session "Upper" {
                    do BenchPress sets 4 reps 6 load bench_1rm * 0.75 rpe 8;
                    rest 150;
                    circuit rounds 3 {
                        do Row sets 1 reps 10 load 60.0;
                        do PullUp sets 1 reps 6 load 10.0;
                        rest 90;
                    }
                }
            }
        }
        week 2 {
            monday {
                session "Lower" {
                    do Squat sets 4 reps 5 load squat_1rm * 0.75 + 5.0 rpe 8;
                    rest 180;
                    do RomanianDeadlift sets 3 reps 8 load 95.0 rpe 7;
                }
            }
            thursday {
                session "Upper" {
                    repeat 4 times {
                        do BenchPress sets 1 reps 6 load bench_1rm * 0.75 + 2.5 rpe 8;
                        rest 150;
                    }
                }
            }
        }
    }
}