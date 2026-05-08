import { auth } from "@clerk/nextjs/server";
import { clerkClient } from "@clerk/nextjs/server";
import { stripe } from "@/lib/stripe";

export async function POST(req: Request) {
  const { userId } = await auth();
  if (!userId) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { priceId } = await req.json();
  if (!priceId) {
    return Response.json({ error: "Missing priceId" }, { status: 400 });
  }

  const client = await clerkClient();
  const user = await client.users.getUser(userId);
  let stripeCustomerId = user.privateMetadata?.stripeCustomerId as string | undefined;

  if (!stripeCustomerId) {
    const customer = await stripe.customers.create({
      email: user.emailAddresses[0]?.emailAddress,
      metadata: { clerkUserId: userId },
    });
    stripeCustomerId = customer.id;
    await client.users.updateUserMetadata(userId, {
      privateMetadata: { stripeCustomerId },
    });
  }

  const session = await stripe.checkout.sessions.create({
    customer: stripeCustomerId,
    mode: "subscription",
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard/picks?success=1`,
    cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/pricing`,
    subscription_data: {
      metadata: { clerkUserId: userId },
    },
  });

  return Response.json({ url: session.url });
}
