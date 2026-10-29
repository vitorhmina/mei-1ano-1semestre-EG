program Bad {
    exercise Squat { category: "lower" }
    routine R {
        week 1 {
            session "Mon" {
                do Deadlift sets 3 reps 5;
                do Squat sets 3 reps 5 rpe 15;
                var x : int = "heavy";
                last_rpe = 7.0;
            }
        }
        week 3 { session "Mon" { rest 60; } }
    }
}
