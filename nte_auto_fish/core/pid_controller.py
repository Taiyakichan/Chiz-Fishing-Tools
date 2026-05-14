import time
from typing import Optional

class PIDController:
    """Advanced PID controller with velocity feedforward and edge aggression."""
    
    def __init__(
        self,
        kp: float = 0.5,
        ki: float = 0.05,
        kd: float = 0.1,
        ff_weight: float = 0.15,
        integral_limit: float = 1.0,
        deadband: float = 0.01
    ):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.ff_weight = ff_weight
        self.integral_limit = integral_limit
        self.deadband = deadband
        
        self.reset()

    def reset(self):
        self._prev_error = 0.0
        self._integral = 0.0
        self._last_time: Optional[float] = None
        self._last_target: Optional[float] = None
        self._target_velocity = 0.0

    def update(self, current: float, target: float, bar_width: float = 1.0) -> float:
        """
        Calculate the next PID output. 
        Expects current and target as normalized values (0.0 to 1.0).
        """
        now = time.time()
        if self._last_time is None:
            dt = 0.01
        else:
            dt = now - self._last_time
        
        if dt <= 0:
            dt = 0.001
            
        self._last_time = now
        
        # --- Error Calculation ---
        error = target - current
        if abs(error) < self.deadband:
            error = 0.0
            
        # --- Velocity Estimation (Feedforward) ---
        if self._last_target is not None:
            raw_vel = (target - self._last_target) / dt
            # Simple alpha smoothing for velocity
            self._target_velocity = self._target_velocity * 0.7 + raw_vel * 0.3
        self._last_target = target
        
        # --- PID Terms ---
        p_term = self.kp * error
        
        self._integral += error * dt
        self._integral = max(-self.integral_limit, min(self.integral_limit, self._integral))
        i_term = self.ki * self._integral
        
        d_term = self.kd * (error - self._prev_error) / dt
        self._prev_error = error
        
        ff_term = self._target_velocity * self.ff_weight
        
        # --- Edge Aggression ---
        # If either cursor or target are near the edges, we increase P-gain 
        # to prevent "escaping" the bar.
        edge_multiplier = 1.0
        edge_threshold = 0.15 # 15% from edges
        dist_to_edge = min(current, 1.0 - current, target, 1.0 - target)
        if dist_to_edge < edge_threshold:
            # Linear increase up to 1.5x gain at the very edge
            edge_multiplier = 1.5 - (dist_to_edge / edge_threshold) * 0.5
            
        output = (p_term + i_term + d_term + ff_term) * edge_multiplier
        return output
