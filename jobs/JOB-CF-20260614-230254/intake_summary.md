# Cloudflare Email Intake

- Job ID: JOB-CF-20260614-230254
- From: "Joe Metz" <joe.metz.psu@gmail.com>
- To: info@jupiterembroideryco.com
- Subject: Embiz real email test 2
- Received: 2026-06-14T23:02:54.877689

## Body

Received: from mail-yw1-x112d.google.com (2607:f8b0:4864:20::112d)
        by cloudflare-email.net (cloudflare) id GY1KdjWjOU9O
        for <info@jupiterembroideryco.com>; Sun, 14 Jun 2026 21:02:54 +0000
ARC-Seal: i=2; a=rsa-sha256; s=cf2024-1; d=cloudflare-email.net; cv=pass;
	b=Wi8X+MkR1MkjvW9MGReK5nh1R8e6/uVio3XL4ksg3hajODOUN46CCEpehDS5Sc1DLupbclu4n
	/xoDRI+YjYWwmnmFGd4ZBcsnG8VWA6gMps11mQ/+VOA9Ct+N02mTgqCjwX6wvsJZ7/vJVpj3Ycg
	yhkqGpx04EFqxmlfGxvzQ/KPGtLJjaSpRtpQpjuc7rwIiXaeZBvsykHTqoubPOpvm+Jgogff/X0
	viyID4sI9wiOxEkHqyH12SsjnoDIhiICIRwHUvMSyEBPx6BWsLptjgQJlec1zCMT568n5Ev2o/T
	85F4x8MkikWk0Lui4jIHyp+HGrMnLbV1ABBd5WLiAogQ==;
ARC-Message-Signature: i=2; a=rsa-sha256; s=cf2024-1; d=cloudflare-email.net; c=relaxed/relaxed;
	h=To:Subject:Date:From:from:reply-to:cc:resent-date:resent-from:resent-to
	:resent-cc:in-reply-to:references:list-id:list-help:list-subscribe
	:list-post:list-owner:list-archive; t=1781470974; x=1782075774; bh=9flxvThO
	KDWRnxJaGZ4/6JrDScAxqARqKsy7d+DdzJY=; b=RAHcvgMtMg4N27VLi74GA7DGm64ivR4t6Du
	gNjNogl4/DopUQc2RYKgoeYLfyBXn7b9Whsa0+exEolVMEsX7J/U9CIQ4MjrJjCz6CCLxJovbhD
	4Fsfjb5GNa2aO4pQNXyp9wvfuGtwT9mjS76xM8Q3Ezrv2G/rQsmHcgraf8egjoNWkdFvYvAQwbJ
	5J5ue5GKhtXahQ72zrLRhqD/pgl5E3n8VdhR0LiTiSZ2kL3uZuX4/mDKpv6i0RFX4u0Cqju6S+i
	ZKoo8nOs/qKdJUs6RWEf9XQ3617hUMIm7fl2u1U6/vLI2pCrhfR9q1EQ+GbfiO/+upSvA/eVK0d
	va1VbOQ==;
ARC-Authentication-Results: i=2; mx.cloudflare.net;
	dkim=pass header.d=gmail.com header.s=20251104 header.b=L6CZ3OJ0;
	dmarc=pass header.from=gmail.com policy.dmarc=none;
	spf=none (mx.cloudflare.net: no SPF records found for postmaster@mail-yw1-x112d.google.com) smtp.helo=mail-yw1-x112d.google.com;
	spf=pass (mx.cloudflare.net: domain of joe.metz.psu@gmail.com designates 2607:f8b0:4864:20::112d as permitted sender) smtp.mailfrom=joe.metz.psu@gmail.com;
	arc=pass smtp.remote-ip="2607:f8b0:4864:20::112d"
Received-SPF: pass (mx.cloudflare.net: domain of joe.metz.psu@gmail.com designates 2607:f8b0:4864:20::112d as permitted sender)
	receiver=mx.cloudflare.net; client-ip=2607:f8b0:4864:20::112d; envelope-from="joe.metz.psu@gmail.com"; helo=mail-yw1-x112d.google.com;
Authentication-Results: mx.cloudflare.net;
	dkim=pass header.d=gmail.com header.s=20251104 header.b=L6CZ3OJ0;
	dmarc=pass header.from=gmail.com policy.dmarc=none;
	spf=none (mx.cloudflare.net: no SPF records found for postmaster@mail-yw1-x112d.google.com) smtp.helo=mail-yw1-x112d.google.com;
	spf=pass (mx.cloudflare.net: domain of joe.metz.psu@gmail.com designates 2607:f8b0:4864:20::112d as permitted sender) smtp.mailfrom=joe.metz.psu@gmail.com;
	arc=pass smtp.remote-ip="2607:f8b0:4864:20::112d"
Received: by mail-yw1-x112d.google.com with SMTP id 00721157ae682-7e053987001so37794367b3.0
        for <info@jupiterembroideryco.com>; Sun, 14 Jun 2026 14:02:54 -0700 (PDT)
ARC-Seal: i=1; a=rsa-sha256; t=1781470974; cv=none;
        d=google.com; s=arc-20240605;
        b=JYPNcwkp+of5J+H/IpLnw6TA5xX66U45MyUhkc++cXnucFyo5IlMapIcvJkTm7Bo/O
         gGM7eYVvq4wXrj7H7875/vFDmSK0VVd1t+zCW1vnAHPDujnd+OrPwN1oblPeLtRq6y1U
         zjQ2hIcZe4R/fXGfbZik0EvXp5OVxoe63HMiBZlbpLZ3v1gPCJSYvtAzcg7o4jRb5RKY
         +VkQaZTkagSN3jJd5iVQbLwjW4cuxzADaYvH3b34i+xQTJ+DB2KJkWuMVF1mFIXRiU9E
         ++LpAjHEsyiRbmthCLGG9TH6sm6HfxoO2pJ/XuLF3maENm3UKfA4843gs4jl5AdowBpm
         23TQ==
ARC-Message-Signature: i=1; a=rsa-sha256; c=relaxed/relaxed; d=google.com; s=arc-20240605;
        h=to:subject:message-id:date:from:mime-version:dkim-signature;
        bh=9flxvThOKDWRnxJaGZ4/6JrDScAxqARqKsy7d+DdzJY=;
        fh=h3LRHuEbBG0F+ueycRmwuVXOKjTIGKw6O5m+yczeTfM=;
        b=NFJXyuH6RvaABHar+FMCX8LmQjm8c1IHAcMmCTqGFUWiXVlJDfS3dLM2GfYr/Kwx/v
         9N3aTtMTCiaFOUR+jnIm0n9OWhr+8O8MBjVOva+EHYgQQY5rLPBV7fx2WDQVOUv95SnS
         vLVB5gRf4ecDQJVIxeElKeRewhHgRK7k7IOeU6ESWV/6yf+eZw+Nz26k6iNdv7ssyYnd
         FFWSGuNhJ8aeESHiP+cW0Enz+W04Sq3nTEA4E/3HqmegD9K74uv6fKbb1olJe+VfG99Y
         KeA9PwCz6m3iZSQQJn+C1oK7yMTw3veuxrMxdkNjjUuV80WT034FSRtg7nF+PW94IoHe
         BV0Q==;
        darn=jupiterembroideryco.com
ARC-Authentication-Results: i=1; mx.google.com; arc=none
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;
        d=gmail.com; s=20251104; t=1781470974; x=1782075774; darn=jupiterembroideryco.com;
        h=to:subject:message-id:date:from:mime-version:from:to:cc:subject
         :date:message-id:reply-to;
        bh=9flxvThOKDWRnxJaGZ4/6JrDScAxqARqKsy7d+DdzJY=;
        b=L6CZ3OJ09jjyZ14s2N7U0ynGmNXg+U7GiSUXgk13fT3IoQaZRPB80K0g5zFvSdlJnS
         z3PEy+imAwUEEDaxhNLSPrSZ9PR0krQWLDVWZjxVceQQGtF1im/4E53DjWAEXJQWGlrf
         7aVLNKXqUETUHIqaQ7ju6RLBlENTPKJw8Sx+r8rsWEU+GuwoBIxqvi+MZJKCxXQO2nz5
         xjJs4z4I8ozt4P2Bs4fyHpHfLrjUYhI/G95WRxIFSGSbl6hJRo97uG+/bKOMbFLdPm4l
         CwsDGajBre1Bs+meRgyegTmoK/keXrtneIpNztDBMnD1DKJiOpmA2MOZhtWptpvyQomQ
         iJVg==
X-Google-DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;
        d=1e100.net; s=20251104; t=1781470974; x=1782075774;
        h=to:subject:message-id:date:from:mime-version:x-gm-gg
         :x-gm-message-state:from:to:cc:subject:date:message-id:reply-to;
        bh=9flxvThOKDWRnxJaGZ4/6JrDScAxqARqKsy7d+DdzJY=;
        b=rOvOG10T5I8M6rl7JcDlcypvKsRwrE65c7AfZ1rcIv1QQaRpNcKjJ9+IPlARJ3VY+p
         NBxZNn5C/3ERWnu77Tl0Iu+N9jwvbHSJy6q6l9/1oSDp40zmolsYriQUu4QOWT0+X2ca
         FF6HEjeomhpXRzuvPfFoepthaD5Fw5PS7h61buLz1jslz1ZGF7/dZM2mHJOZ4DjKI/jB
         ACjQ0OB3fUA7zplRlSXdmy7cqBPZvcqLInKoYJ9NYCc8vbyaW2blOaHTI8CcbigNCiw5
         x+lh+F2tCWXCAF7PTY45AtK/BOulJ5s81v/9gd5xK9UdPnuLsrRmOhCfuiJKArq/PZRO
         dplA==
X-Gm-Message-State: AOJu0YykNDMbs7Q0o4E+RH1zzet3QStxBvj1P0SpIPcXb/Y+qokagXa+
	45b7e29zBeIJs+pnt/6hIMhjMj5q293t8GFr4yCNWuCEV926YzdygNQcFUuwJ9UP3Sb3NMdvNz4
	TCC5ZmnsmQcwEk0kstCt4VUp3qUB6qShU/N574jc=
X-Gm-Gg: Acq92OHjd7lYtKAcXa2PooOH2UASf8knTxAYqAbG6k8Oc1Y2jZ3PpplpfObw5b6+v+m
	DMBVNUFun/m6NvXwaYGiJS6vOd9EzATyYyUrUZsaihJM8qXvy2lr3hGw5VC1LqLFIyQ9037hIQa
	We8joKv4HB6FRpAH3VWUiuqbwDbkWTVmlTLBLp3DCMyb9qRy+WCWxclEk2YUhHvxfTrFfNULpIw
	2l/1nT265UD+/LrqtHFG7ciFTaUTyZ6UruBMhYlYG1fC0t1t6RqmypaWgZe5kY04PhLctW6TKNL
	D3Fim0uFXhY13pgKMRN1NHdR+U/Q/qMrTWbsuWI5UQsDc/1we5PrzZjQhXdraAOtWPpf70Ev
X-Received: by 2002:a05:690e:144b:b0:660:e9fe:18e9 with SMTP id
 956f58d0204a3-66276aff4admr8286120d50.38.1781470974170; Sun, 14 Jun 2026
 14:02:54 -0700 (PDT)
MIME-Version: 1.0
From: Joe Metz <joe.metz.psu@gmail.com>
Date: Sun, 14 Jun 2026 17:02:17 -0400
X-Gm-Features: AVVi8CcaeSmpxmkFS6S_AhvOF6i-sKQPe9-A8YW2eZxqIfBkeBD6tJnNhhKVOYg
Message-ID: <CAD+nXsvZFoWO-PizaT3QkZWPUrJKr__aKWSzBZyaWd_Kjg0Tfw@mail.gmail.com>
Subject: Embiz real email test 2
To: info@jupiterembroideryco.com
Content-Type: multipart/alternative; boundary="00000000000097db1206543d08fd"

--00000000000097db1206543d08fd
Content-Type: text/plain; charset="UTF-8"
Content-Transfer-Encoding: quoted-printable

Hi,

I=E2=80=99m looking for a quote for embroidery on 18 black polo shirts.

Details:

   -

   Left chest logo placement
   -

   Logo is about 3.5 inches wide
   -

   Thread colors: white and light blue
   -

   Needed within 2 weeks if possible
   -

   I can send the logo file after you confirm the best format

Please let me know what else you need from me to quote this.

Thanks,
Test Customer


--=20


Thanks!
Joe
cell: 717-8024404

--00000000000097db1206543d08fd
Content-Type: text/html; charset="UTF-8"
Content-Transfer-Encoding: quoted-printable

<div dir=3D"ltr"><div><div style=3D"font-size:small" class=3D"gmail_default=
"><p>Hi,</p><p>I=E2=80=99m looking for a quote for embroidery on 18 black p=
olo shirts.</p><p>Details:</p><ul><li><p>Left chest logo placement</p></li>=
<li><p>Logo is about 3.5 inches wide</p></li><li><p>Thread colors: white an=
d light blue</p></li><li><p>Needed within 2 weeks if possible</p></li><li><=
p>I can send the logo file after you confirm the best format</p></li></ul><=
p>Please let me know what else you need from me to quote this.</p><p>Thanks=
,<br>Test Customer</p></div><br clear=3D"all"></div><br><span class=3D"gmai=
l_signature_prefix">-- </span><br><div dir=3D"ltr" class=3D"gmail_signature=
" data-smartmail=3D"gmail_signature"><div dir=3D"ltr"><br><div><br></div><d=
iv>Thanks!</div><div>Joe</div><div>cell: 717-8024404</div><div><br></div><d=
iv><br></div></div></div></div>

--00000000000097db1206543d08fd--

