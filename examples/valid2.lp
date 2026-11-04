program FullBody {
    exercise Squat  { category: "lower" }
    exercise PullUp { category: "upper", equipment: "bodyweight" }

    routine Basics {
        week 1 {
            monday {
                session "Morning" {
                    repeat 3 times {
                        do Squat sets 1 reps 8 load 60.0 rpe 7;
                        rest 120;
                    }
                }
                session "Evening" {
                    do PullUp sets 3 reps 6 load 5.0;
                    rest 90;
                }
            }
        }
    }
}