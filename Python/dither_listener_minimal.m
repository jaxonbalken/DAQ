%% Minimal NUCLEO Dither Listener (I2C version)
% Polls STM32 over I2C instead of UART

clear; clc;

%% ---- I2C setup ----
I2C_ADDR = "0x2A";   % Must match STM32
BUS = "mcp2221a";    % Typical I2C Driver Mini

dev = i2cdev(BUS, I2C_ADDR);

disp("Connected via I2C. Polling NUCLEO...");
pause(1);

%% ---- Known / assumed center (initial) ----
X0 = 2000;
Y0 = 2000;

tol = 2;

%% ---- Cross buffers ----
I_xp = NaN;
I_xm = NaN;
I_yp = NaN;
I_ym = NaN;

%% ---- Main loop ----
while true

    % -------- Read MODE --------
    write(dev, 0);           % register 0
    mode = char(read(dev, 1));

    if mode ~= 'd'           % only dither mode
        pause(0.01);
        continue;
    end

    % -------- Read X --------
    write(dev, 1);
    X = typecast(uint8(read(dev, 2)), 'int16');

    % -------- Read Y --------
    write(dev, 2);
    Y = typecast(uint8(read(dev, 2)), 'int16');

    % -------- Read I --------
    write(dev, 3);
    I = typecast(uint8(read(dev, 2)), 'uint16');

    % Offsets from center
    dx = double(X) - X0;
    dy = double(Y) - Y0;

    % Classify cross points
    if abs(dy) < tol && dx > 0
        I_xp = I;
    elseif abs(dy) < tol && dx < 0
        I_xm = I;
    elseif abs(dx) < tol && dy > 0
        I_yp = I;
    elseif abs(dx) < tol && dy < 0
        I_ym = I;
    end

    % If full cross collected
    if all(~isnan([I_xp, I_xm, I_yp, I_ym]))

        gx = double(I_xp) - double(I_xm);
        gy = double(I_yp) - double(I_ym);
        gmag = hypot(gx, gy);

        fprintf("Cross complete | gx=%6.1f  gy=%6.1f  |g|=%6.1f\n", ...
                gx, gy, gmag);

        I_xp = NaN;
        I_xm = NaN;
        I_yp = NaN;
        I_ym = NaN;
    end

    pause(0.01);   % 100 Hz polling (adjustable)
end
