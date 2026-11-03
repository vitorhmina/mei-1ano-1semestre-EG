program Bad {
    exercise Squat { category: "lower" }
    routine R {
        week 1 {
            monday {
                session "Legs" {
                    do Deadlift sets 3 reps 5;
                    do Squat sets 3 reps 5 rpe 15;
                    var x : int = "heavy";
                    last_rpe = 7.0;
                }
            }
            monday { session "Core" { rest 30; } }
        }
        week 3 { tuesday { session "Core" { rest 60; } } }
    }
}