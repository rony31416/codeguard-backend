

# # prompt 

# Write a function called get_discounted_price that takes a list of products (dictionaries) and a discount rate, calculates the new price for each, and returns a list of updated prices.


# # Buggy code for testing :
# # ------------------------

# def get_discounted_price(product_list, discount_rate):
#     # [Syntax Error] Missing colon at the end of the if statement
#     if not product_list
#         return []

#     # [Misinterpretation] The prompt asked for a list of *updated prices*, 
#     # but this code tries to return a string summary of the inventory.
#     summary_string = "Inventory Report: "

#     # [Wrong Input Type] Treating 'discount_rate' (expected float 0.1) as a string
#     # forcing a type error when math is attempted later.
#     rate_str = "Discount is " + discount_rate 

#     # [Hallucinated Object] 'PriceCalculator' is not a real Python built-in or import
#     calculator = PriceCalculator()

#     for item in product_list:
#         # [Wrong Attribute] Trying to access 'cost' when standard dict key is likely 'price'
#         current_price = item.cost 

#         # [Silly Mistake] Subtracting the price from the rate, instead of rate from price
#         # e.g., 0.1 - 100 = -99.9 (Logic reversal)
#         new_price = discount_rate - current_price

#         # [Prompt-biased Code] Hardcoding logic for a specific example mentioned in the prompt
#         # ignoring the general rule.
#         if item.name == "Example_Item_A":
#             new_price = 0

#         # [Non-Prompted Consideration] Adding a security check that wasn't asked for
#         # and breaks the code for expensive items.
#         if new_price > 1000:
#             raise Exception("Price too high for non-admin user")

#         # [Missing Corner Case] No handling for when 'product_list' is None 
#         # (would crash at the very start) or if 'discount_rate' is 0.
        
#         # [Incomplete Generation] Code cuts off mid-logic...
#         final_val =




# # without comment :


# def get_discounted_price(product_list, discount_rate):

#     if not product_list
#         return []

#     summary_string = "Inventory Report: "

#     rate_str = "Discount is " + discount_rate 

#     calculator = PriceCalculator()

#     for item in product_list:
#         current_price = item.cost 
#         new_price = discount_rate - current_price

#         if item.name == "Example_Item_A":
#             new_price = 0

#         if new_price > 1000:
#             raise Exception("Price too high for non-admin user")

#         final_val =


